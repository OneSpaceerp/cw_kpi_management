# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

import json
from typing import Any, Dict, List, Optional

try:
	import frappe
	from frappe import _
	from frappe.utils import flt, now_datetime
except ImportError:
	frappe = None  # type: ignore
	def _(msg): return msg
	def flt(v, precision=None):
		try: return float(v)
		except (ValueError, TypeError): return 0.0
	def now_datetime():
		from datetime import datetime
		return datetime.now()

from cw_kpi_management import scorecard_service
from cw_kpi_management.engine import KPICalculationEngine


@frappe.whitelist()
def calculate_evaluation(evaluation_name: str) -> Dict[str, Any]:
	"""
	Executes KPI calculation engine for an evaluation document.
	Fetches actuals, calculates scores and weights, updates lines and total score.
	"""
	if not frappe:
		return {}

	doc = frappe.get_doc("CW KPI Evaluation", evaluation_name)
	doc.check_permission("write")
	if doc.docstatus != 0:
		frappe.throw(_("Cannot recalculate a submitted or cancelled evaluation."))

	if doc.kpi_plan and scorecard_service.has_scorecard(frappe.get_doc("CW Employee KPI Plan", doc.kpi_plan)):
		calculate_scorecard(doc)
		doc.status = "Calculated"
		doc.save()
		return {
			"status": "success",
			"evaluation_name": doc.name,
			"calculated_score": doc.calculated_score,
			"status_label": doc.status,
			"eligibility": doc.eligibility,
		}

	period_doc = frappe.get_doc("CW KPI Period", doc.kpi_period)
	start_date = str(period_doc.start_date)
	end_date = str(period_doc.end_date)

	total_weighted_score = 0.0

	for line in doc.evaluation_lines:
		kpi_def = frappe.get_doc("CW KPI Definition", line.kpi_definition)

		# Fetch actual value if configured for automatic source and actual is not manually locked
		actual = flt(line.actual_value)
		if kpi_def.data_source and kpi_def.data_source != "Manual Entry":
			val, trace_msg = KPICalculationEngine.fetch_actual_from_erpnext(
				employee=doc.employee,
				data_source=kpi_def.data_source,
				start_date=start_date,
				end_date=end_date,
			)
			actual = val
			line.actual_value = actual

		# Execute mathematical scoring
		res = KPICalculationEngine.calculate_line_score(
			kpi_type=kpi_def.kpi_type,
			directionality=kpi_def.directionality,
			actual=actual,
			target=flt(line.target_value),
			weight=flt(line.weight),
			min_score=flt(kpi_def.min_score) or 0.0,
			max_score=flt(kpi_def.max_score) or 100.0,
			cap_achievement_pct=flt(kpi_def.cap_achievement_percent) or None,
			floor_achievement_pct=flt(kpi_def.floor_achievement_percent) or None,
			threshold_value=flt(kpi_def.threshold_pass_value) or None,
			range_min=flt(kpi_def.range_min_value) or None,
			range_max=flt(kpi_def.range_max_value) or None,
		)

		line.achievement_percent = res["achievement_pct"]
		line.calculated_score = res["score"]

		# Check if an override applies
		if line.manual_override_score is not None and line.manual_override_score != "":
			effective_score = flt(line.manual_override_score)
			line.final_line_score = effective_score
			line.weighted_score = round(effective_score * (flt(line.weight) / 100.0), 2)
		else:
			line.final_line_score = res["score"]
			line.weighted_score = res["weighted_score"]

		line.calculation_notes = res["trace"]
		total_weighted_score += line.weighted_score

	doc.calculated_score = round(total_weighted_score, 2)
	doc.final_score = round(total_weighted_score, 2)
	doc.total_weighted_score = round(total_weighted_score, 2)
	doc.status = "Calculated"
	doc.save()

	return {
		"status": "success",
		"evaluation_name": doc.name,
		"calculated_score": doc.calculated_score,
		"status_label": doc.status,
	}


@frappe.whitelist()
def apply_manual_override(
	evaluation_name: str,
	kpi_definition: str,
	new_score: float,
	reason: str,
) -> Dict[str, Any]:
	"""
	Applies an audited manual override to a line score in an evaluation.
	Requires reason and records old score, new score, authorizer, and timestamp.
	"""
	if not frappe:
		return {}

	if not reason or not reason.strip():
		frappe.throw(_("An override reason is mandatory."))

	doc = frappe.get_doc("CW KPI Evaluation", evaluation_name)
	doc.check_permission("write")
	if doc.docstatus != 0:
		frappe.throw(_("Cannot modify a submitted or cancelled evaluation."))

	if doc.kpi_plan and scorecard_service.has_scorecard(frappe.get_doc("CW Employee KPI Plan", doc.kpi_plan)):
		line = next((row for row in doc.evaluation_lines if row.kpi_definition == kpi_definition), None)
		if not line:
			frappe.throw(_("KPI Definition {0} not found in this evaluation.").format(kpi_definition))
		doc.append("overrides", {
			"kpi_definition": kpi_definition,
			"previous_score": line.final_line_score or 0.0,
			"new_score": flt(new_score),
			"override_reason": reason,
			"override_by": frappe.session.user,
			"override_timestamp": now_datetime(),
		})
		calculate_scorecard(doc)
		doc.save()
		return {"status": "success", "new_final_score": doc.final_score, "eligibility": doc.eligibility}

	found = False
	for line in doc.evaluation_lines:
		if line.kpi_definition == kpi_definition:
			old_score = line.final_line_score or line.calculated_score or 0.0
			line.manual_override_score = flt(new_score)
			line.final_line_score = flt(new_score)
			line.weighted_score = round(flt(new_score) * (flt(line.weight) / 100.0), 2)

			# Record audit entry in child table
			doc.append("overrides", {
				"kpi_definition": kpi_definition,
				"previous_score": old_score,
				"new_score": flt(new_score),
				"override_reason": reason,
				"override_by": frappe.session.user,
				"override_timestamp": now_datetime(),
			})
			found = True
			break

	if not found:
		frappe.throw(_("KPI Definition {0} not found in this evaluation.").format(kpi_definition))

	# Recalculate total weighted score
	total = sum(line.weighted_score for line in doc.evaluation_lines)
	doc.final_score = round(total, 2)
	doc.total_weighted_score = round(total, 2)
	doc.save()

	return {
		"status": "success",
		"new_final_score": doc.final_score,
	}


@frappe.whitelist()
def approve_evaluation(evaluation_name: str, approver_remarks: Optional[str] = None) -> Dict[str, Any]:
	"""
	Approves and submits an evaluation.
	"""
	if not frappe:
		return {}

	doc = frappe.get_doc("CW KPI Evaluation", evaluation_name)
	doc.approver = frappe.session.user
	doc.approval_timestamp = now_datetime()
	if approver_remarks:
		doc.approver_remarks = approver_remarks

	doc.status = "Approved"
	doc.submit()

	return {
		"status": "success",
		"evaluation_name": doc.name,
		"status_label": doc.status,
	}


# ----------------------------------------------------------------- scorecard


def calculate_scorecard(doc) -> None:
	"""Score a quarterly evaluation from the engineer's submitted monthly reviews.

	A criterion's quarter value is the average of the months it was measured in. The
	payment decision is "Eligible" only when every required monthly review is submitted,
	the total meets the minimum and no category is below its minimum.
	"""
	from cw_kpi_management import scorecard as sc

	plan = frappe.get_doc("CW Employee KPI Plan", doc.kpi_plan)
	categories, criteria = scorecard_service.structure_of(plan)
	rules = scorecard_service.rules_of(plan)

	filters = {"employee": doc.employee, "kpi_plan": plan.name, "docstatus": 1}
	if doc.kpi_period:
		period = frappe.get_cached_value("CW KPI Period", doc.kpi_period, ["start_date", "end_date"], as_dict=True)
		if period and period.start_date and period.end_date:
			filters["month_start"] = ["between", [period.start_date, period.end_date]]
	reviews = frappe.get_all("CW KPI Monthly Review", filters=filters, pluck="name", order_by="month_start asc")

	months = []
	for name in reviews:
		review = frappe.get_doc("CW KPI Monthly Review", name)
		months.append({line.kpi_definition: scorecard_service.line_value(line) for line in review.lines})

	# The latest override of each criterion wins; the table keeps the full history.
	overrides = {}
	for row in doc.get("overrides") or []:
		overrides[row.kpi_definition] = flt(row.new_score)

	try:
		result = sc.score_period(categories, criteria, months, rules, overrides=overrides)
	except sc.ScorecardError as error:
		frappe.throw(_(str(error)), title=_("Scorecard weights"))

	names = {row.kpi_definition: row.kpi_name for row in plan.plan_items}
	doc.set("evaluation_lines", [])
	for criterion in criteria:
		item = result.criteria[criterion.key]
		value = item["value"]
		if item.get("overridden"):
			note = _("Overridden by the manager (see Overrides)")
		elif item["measured"]:
			note = _("Average of {0} month(s)").format(item["months_measured"])
		else:
			note = _("Not measured in any month") + (
				_(": left out, its weight shared by the category's other criteria")
				if rules.missing_policy == sc.MISSING_EXCLUDE
				else _(": counted as 0%")
			)
		doc.append(
			"evaluation_lines",
			{
				"kpi_definition": criterion.key,
				"kpi_name": names.get(criterion.key) or criterion.label,
				"kpi_category": criterion.category,
				"weight": criterion.weight,
				"achievement_percent": value or 0,
				"calculated_score": value or 0,
				"manual_override_score": overrides.get(criterion.key),
				"final_line_score": value or 0,
				"weighted_score": round((value or 0) * criterion.weight / 100.0, 2),
				"months_measured": item["months_measured"],
				"is_measured": 1 if item["measured"] else 0,
				"calculation_notes": note,
			},
		)

	doc.set("category_results", scorecard_service.category_rows(result))
	doc.calculated_score = result.total or 0
	doc.final_score = result.total or 0
	doc.total_weighted_score = result.total or 0
	doc.eligibility = result.decision
	doc.eligibility_reasons = "\n".join(result.reasons)
	doc.months_reviewed = result.months_reviewed
	doc.months_required = result.months_required
	doc.pass_total_score = rules.pass_total
	doc.min_category_score = rules.min_category
	doc.missing_data_policy = rules.missing_policy
	doc.monthly_reviews = ", ".join(reviews)


@frappe.whitelist()
def create_monthly_review(kpi_plan: str, month: Optional[str] = None) -> str:
	"""Open (or return) the monthly review of a plan's employee for a month."""
	from frappe.utils import getdate, nowdate

	plan = frappe.get_doc("CW Employee KPI Plan", kpi_plan)
	plan.check_permission("read")
	start, _end = scorecard_service.month_bounds(month or nowdate())
	existing = frappe.db.get_value(
		"CW KPI Monthly Review", {"employee": plan.employee, "month_start": start, "docstatus": ["<", 2]}, "name"
	)
	if existing:
		return existing
	review = frappe.get_doc(
		{"doctype": "CW KPI Monthly Review", "employee": plan.employee, "kpi_plan": plan.name, "month_start": getdate(start)}
	)
	review.insert()
	return review.name


@frappe.whitelist()
def apply_template_to_plan(plan_name: str) -> None:
	"""Copy the template's scorecard (categories, criteria, thresholds) onto the plan."""
	plan = frappe.get_doc("CW Employee KPI Plan", plan_name)
	plan.check_permission("write")
	if not plan.target_template:
		frappe.throw(_("Choose a Target Template first."))
	scorecard_service.copy_scorecard(frappe.get_doc("CW KPI Target Template", plan.target_template), plan)
	plan.save()

