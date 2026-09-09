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
	if doc.docstatus != 0:
		frappe.throw(_("Cannot recalculate a submitted or cancelled evaluation."))

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
	if doc.docstatus != 0:
		frappe.throw(_("Cannot modify a submitted or cancelled evaluation."))

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
