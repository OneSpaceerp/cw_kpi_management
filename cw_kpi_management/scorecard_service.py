# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

"""Frappe side of the scorecard: documents in, `scorecard` engine, documents out.

A template or plan "has a scorecard" when its Categories table is filled in. Plans
without categories keep working the old way (one flat list of weighted KPIs).
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, get_first_day, get_last_day, getdate

from cw_kpi_management import scorecard as sc
from cw_kpi_management import sources

SETTINGS = "CW KPI Settings"


def has_scorecard(doc) -> bool:
	return bool(doc.get("categories"))


def items_of(doc):
	return doc.get("plan_items") if doc.doctype == "CW Employee KPI Plan" else doc.get("template_items")


def settings():
	return frappe.get_cached_doc(SETTINGS)


def rules_of(doc) -> sc.Rules:
	"""Thresholds from the plan or template, falling back to CW KPI Settings."""
	s = settings()
	return sc.Rules(
		pass_total=flt(doc.get("pass_total_score") or s.get("default_pass_total_score") or 85),
		min_category=flt(doc.get("min_category_score") or s.get("default_min_category_score") or 70),
		missing_policy=doc.get("missing_data_policy") or s.get("default_missing_data_policy") or sc.MISSING_EXCLUDE,
		months_required=cint(doc.get("months_required") or s.get("default_months_required") or 3),
		precision=cint(s.get("score_precision") if s.get("score_precision") not in (None, "") else 1),
	)


def structure_of(doc):
	"""(categories, criteria) of a plan or template."""
	categories = [
		sc.Category(
			key=row.kpi_category,
			weight=flt(row.weight),
			min_score=flt(row.min_score) if row.get("min_score") not in (None, "", 0) else None,
			label=row.kpi_category,
		)
		for row in doc.get("categories") or []
	]
	criteria = []
	allow_above = cint(settings().get("allow_scores_above_100"))
	for row in items_of(doc) or []:
		category = row.get("kpi_category") or frappe.db.get_value("CW KPI Definition", row.kpi_definition, "kpi_category")
		cap = 100.0
		if allow_above:
			cap = flt(frappe.db.get_value("CW KPI Definition", row.kpi_definition, "cap_achievement_percent")) or 100.0
		criteria.append(
			sc.Criterion(key=row.kpi_definition, category=category, weight=flt(row.weight), cap=cap,
						 label=row.get("kpi_name") or row.kpi_definition)
		)
	return categories, criteria


def validate_structure(doc):
	"""Frappe-facing validation for a template or plan with a scorecard."""
	for row in items_of(doc) or []:
		if not row.get("kpi_category"):
			row.kpi_category = frappe.db.get_value("CW KPI Definition", row.kpi_definition, "kpi_category")
	categories, criteria = structure_of(doc)
	try:
		sc.validate(categories, criteria)
	except sc.ScorecardError as error:
		frappe.throw(_(str(error)), title=_("Scorecard weights"))
	if rules_of(doc).missing_policy not in sc.MISSING_POLICIES:
		frappe.throw(_("Choose what a criterion with no data does to the score."))


def copy_scorecard(source, target):
	"""Copy categories, criteria and thresholds from a template to a plan."""
	for field in ("evaluation_cycle", "months_required", "missing_data_policy", "pass_total_score", "min_category_score"):
		target.set(field, source.get(field))
	target.set("categories", [])
	for row in source.get("categories") or []:
		target.append("categories", {"kpi_category": row.kpi_category, "weight": row.weight, "min_score": row.min_score})
	target.set("plan_items", [])
	for row in source.get("template_items") or []:
		target.append(
			"plan_items",
			{
				"kpi_definition": row.kpi_definition,
				"kpi_name": row.kpi_name,
				"kpi_category": row.get("kpi_category"),
				"target_value": row.target_value,
				"weight": row.weight,
				"min_threshold": row.min_threshold,
				"max_threshold": row.max_threshold,
			},
		)


def month_bounds(day):
	day = getdate(day)
	return get_first_day(day), get_last_day(day)


def line_value(line):
	"""A monthly review line's achievement, or None when it was not measured."""
	if cint(line.not_measured):
		return None
	required = flt(line.required_value)
	if required > 0:
		return sc.clamp(flt(line.actual_value) / required * 100.0)
	if line.entry_mode == "Automatic":
		return None  # nothing was required this month
	return sc.clamp(line.achievement_percent)


def category_rows(result: sc.Result) -> list:
	rows = []
	for item in result.categories:
		rows.append(
			{
				"kpi_category": item.key,
				"weight": item.weight,
				"score": item.score,
				"min_score": item.min_score,
				"measured_weight": item.measured_weight,
				"meets_minimum": "Not Measured" if item.meets_minimum is None else ("Yes" if item.meets_minimum else "No"),
			}
		)
	return rows


def refresh_automatic_lines(review):
	"""Fill the automatic criteria of a monthly review from their data source."""
	plan = frappe.get_cached_doc("CW Employee KPI Plan", review.kpi_plan)
	targets = {row.kpi_definition: flt(row.target_value) for row in plan.plan_items}
	for line in review.lines:
		if not sources.is_automatic(line.data_source):
			continue
		measured = sources.measure(
			line.data_source, review.employee, review.month_start, review.month_end, targets.get(line.kpi_definition)
		)
		line.entry_mode = "Automatic"
		line.actual_value = flt(measured["actual"])
		line.required_value = flt(measured["required"])
		line.not_measured = 0 if flt(measured["required"]) > 0 else 1
		line.source_note = measured["note"]


def build_lines(review):
	"""Monthly review lines from the plan's criteria, in category order."""
	plan = frappe.get_doc("CW Employee KPI Plan", review.kpi_plan)
	order = {row.kpi_category: index for index, row in enumerate(plan.categories)}
	review.set("lines", [])
	for row in sorted(plan.plan_items, key=lambda r: (order.get(r.kpi_category, 99), r.idx)):
		definition = frappe.get_cached_value(
			"CW KPI Definition", row.kpi_definition, ["data_source", "measurement_method"], as_dict=True
		) or {}
		automatic = sources.is_automatic(definition.get("data_source"))
		review.append(
			"lines",
			{
				"kpi_definition": row.kpi_definition,
				"kpi_name": row.kpi_name,
				"kpi_category": row.kpi_category,
				"weight": row.weight,
				"data_source": definition.get("data_source") or sources.MANUAL,
				"entry_mode": "Automatic" if automatic else "Manual",
				"source_note": definition.get("measurement_method") or "",
				"not_measured": 0,
			},
		)
	refresh_automatic_lines(review)
