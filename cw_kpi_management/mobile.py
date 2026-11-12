# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

"""The engineer's own scorecard, for the phone app: /api/method/cw_kpi_management.mobile.my_performance

Read-only and personal: the signed-in user sees only the Employee linked to them.

- This month so far: the automatic criteria are measured live (visits, requests,
  feedback, sales); the manager's criteria come from this month's monthly review once
  the manager fills it in, and are "awaiting review" until then. It is a preview: the
  monthly review the manager submits is what counts.
- The quarter: submitted monthly reviews and the latest evaluation's decision.
- Recommendations, ordered by the points they would add to the total.
"""

import frappe
from frappe import _
from frappe.utils import date_diff, flt, getdate, nowdate

from cw_kpi_management import recommendations
from cw_kpi_management import scorecard as sc
from cw_kpi_management import scorecard_service as service
from cw_kpi_management import sources


@frappe.whitelist()
def my_performance() -> dict:
	if frappe.session.user == "Guest":
		frappe.throw(_("Sign in first."), frappe.AuthenticationError)

	employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user, "status": "Active"}, "name")
	if not employee:
		return {"available": False, "reason": "no_employee"}

	plan = _current_plan(employee)
	if not plan:
		return {"available": False, "reason": "no_plan"}

	today = getdate(nowdate())
	month_start, month_end = service.month_bounds(today)
	categories, criteria = service.structure_of(plan)
	rules = service.rules_of(plan)

	review = _month_review(employee, month_start)
	manual = {}
	if review:
		for line in review.lines:
			if line.entry_mode == "Manual":
				manual[line.kpi_definition] = service.line_value(line)

	definitions = {
		row.name: row
		for row in frappe.get_all(
			"CW KPI Definition",
			filters={"name": ["in", [c.key for c in criteria] or [""]]},
			fields=["name", "kpi_name", "arabic_name", "data_source", "measurement_method"],
		)
	}
	targets = {row.kpi_definition: flt(row.target_value) for row in plan.plan_items}

	entries, rows = {}, []
	for criterion in criteria:
		definition = definitions.get(criterion.key) or frappe._dict()
		automatic = sources.is_automatic(definition.data_source)
		actual = required = None
		note = definition.measurement_method or ""
		if automatic:
			measured = sources.measure(definition.data_source, employee, month_start, month_end, targets.get(criterion.key))
			actual, required, note = measured["actual"], measured["required"], measured["note"]
			value = sc.clamp(flt(actual) / flt(required) * 100) if flt(required) > 0 else None
		else:
			value = manual.get(criterion.key)
		entries[criterion.key] = value
		rows.append(
			{
				"code": criterion.key,
				"name": definition.kpi_name or criterion.label,
				"arabic_name": definition.arabic_name,
				"category": criterion.category,
				"weight": criterion.weight,
				"source": definition.data_source,
				"automatic": automatic,
				"actual": actual,
				"required": required,
				"achievement": value,
				"note": note,
			}
		)

	result = sc.score_month(categories, criteria, entries, rules)
	category_meta = {
		row.name: row
		for row in frappe.get_all(
			"CW KPI Category",
			filters={"name": ["in", [c.key for c in categories] or [""]]},
			fields=["name", "arabic_name"],
		)
	}
	category_weights = {c.key: c.weight for c in categories}
	category_rows = [
		{
			"category": item.key,
			"arabic_name": (category_meta.get(item.key) or {}).get("arabic_name"),
			"weight": item.weight,
			"score": item.score,
			"min_score": item.min_score,
			"meets_minimum": item.meets_minimum,
			"measured_weight": item.measured_weight,
		}
		for item in result.categories
	]
	for row in rows:
		row["category_weight"] = category_weights.get(row["category"], 0)

	context = {"days_left": max(date_diff(month_end, today), 0) + 1, **_visit_context(employee, today, month_start, month_end)}
	advice = recommendations.recommend(
		rows, category_rows, {"total": result.total, "pass_total": rules.pass_total}, context
	)

	return {
		"available": True,
		"employee": employee,
		"plan": {"name": plan.name, "period": plan.kpi_period, "template": plan.target_template},
		"rules": {
			"pass_total": rules.pass_total,
			"min_category": rules.min_category,
			"months_required": rules.months_required,
			"missing_policy": rules.missing_policy,
		},
		"month": {
			"start": str(month_start),
			"end": str(month_end),
			"total": result.total,
			"status": result.status,
			"reasons": result.reasons,
			"categories": category_rows,
			"criteria": rows,
			"review": {"name": review.name, "submitted": review.docstatus == 1} if review else None,
		},
		"quarter": _quarter(employee, plan),
		"recommendations": advice,
	}


def _current_plan(employee):
	"""The active scorecard plan whose period covers today, else the newest active one."""
	plans = frappe.get_all(
		"CW Employee KPI Plan",
		filters={"employee": employee, "status": "Active", "docstatus": ["<", 2]},
		fields=["name", "kpi_period"],
		order_by="creation desc",
	)
	today = getdate(nowdate())
	fallback = None
	for row in plans:
		plan = frappe.get_doc("CW Employee KPI Plan", row.name)
		if not service.has_scorecard(plan):
			continue
		fallback = fallback or plan
		if row.kpi_period:
			period = frappe.db.get_value("CW KPI Period", row.kpi_period, ["start_date", "end_date"], as_dict=True)
			if period and period.start_date and getdate(period.start_date) <= today <= getdate(period.end_date):
				return plan
	return fallback


def _month_review(employee, month_start):
	name = frappe.db.get_value(
		"CW KPI Monthly Review", {"employee": employee, "month_start": month_start, "docstatus": ["<", 2]}, "name"
	)
	return frappe.get_doc("CW KPI Monthly Review", name) if name else None


def _quarter(employee, plan) -> dict:
	reviews = frappe.get_all(
		"CW KPI Monthly Review",
		filters={"employee": employee, "kpi_plan": plan.name, "docstatus": 1},
		fields=["month_start", "total_score", "monthly_indicator"],
		order_by="month_start asc",
	)
	evaluation = frappe.get_all(
		"CW KPI Evaluation",
		filters={"employee": employee, "kpi_plan": plan.name, "docstatus": ["<", 2]},
		fields=["name", "eligibility", "final_score", "eligibility_reasons", "months_reviewed", "months_required", "status"],
		order_by="creation desc",
		limit=1,
	)
	latest = evaluation[0] if evaluation else None
	return {
		"period": plan.kpi_period,
		"reviews": [
			{"month": str(r.month_start), "total": r.total_score, "status": r.monthly_indicator} for r in reviews
		],
		"months_required": service.rules_of(plan).months_required,
		"evaluation": {
			"name": latest.name,
			"eligibility": latest.eligibility,
			"total": latest.final_score,
			"reasons": [line for line in (latest.eligibility_reasons or "").split("\n") if line],
			"status": latest.status,
		}
		if latest
		else None,
	}


def _visit_context(employee, today, month_start, month_end) -> dict:
	"""Numbers the recommendations quote: planned visits still ahead, visits without a rating."""
	if "cw_visit" not in frappe.get_installed_apps():
		return {}
	planned_remaining = frappe.db.count(
		"CW Site Visit",
		{
			"assigned_engineer": employee,
			"visit_status": "Planned",
			"docstatus": 0,
			"planned_date": ["between", [today, month_end]],
		},
	)
	executed = frappe.get_all(
		"CW Site Visit",
		filters={
			"assigned_engineer": employee,
			"planned_date": ["between", [month_start, month_end]],
			"visit_status": ["in", ["Pending Review", "Correction Required", "Approved"]],
		},
		fields=["name", "customer_rating"],
	)
	# Started (or sent back) and not handed in: they count only once submitted for review.
	open_visits = frappe.db.count(
		"CW Site Visit",
		{
			"assigned_engineer": employee,
			"docstatus": 0,
			"visit_status": ["in", ["In Progress", "Correction Required"]],
			"planned_date": ["<=", today],
		},
	)
	return {
		"planned_remaining": planned_remaining,
		"visits_without_feedback": sum(1 for visit in executed if not flt(visit.customer_rating)),
		"open_visits": open_visits,
	}
