# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

"""Every engineer's quarter on one row: category scores, total and the payment decision."""

import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	conditions = {"docstatus": ["<", 2], "eligibility": ["is", "set"]}
	for field in ("kpi_period", "department", "employee", "eligibility"):
		if filters.get(field):
			conditions[field] = filters[field]

	evaluations = frappe.get_list(
		"CW KPI Evaluation",
		filters=conditions,
		fields=["name", "employee", "employee_name", "department", "kpi_period", "final_score", "eligibility",
				"months_reviewed", "months_required", "eligibility_reasons", "docstatus"],
		order_by="kpi_period desc, employee_name asc",
		limit=1000,
	)
	results = {}
	for row in frappe.get_all(
		"CW KPI Category Result",
		filters={"parenttype": "CW KPI Evaluation", "parent": ["in", [e.name for e in evaluations] or [""]]},
		fields=["parent", "kpi_category", "score", "meets_minimum"],
	):
		results.setdefault(row.parent, {})[row.kpi_category] = row

	categories = frappe.get_all("CW KPI Category", filters={"is_active": 1}, pluck="name", order_by="creation asc")
	shown = [c for c in categories if any(c in r for r in results.values())]

	columns = [
		{"fieldname": "name", "label": _("Evaluation"), "fieldtype": "Link", "options": "CW KPI Evaluation", "width": 150},
		{"fieldname": "employee_name", "label": _("Engineer"), "fieldtype": "Data", "width": 170},
		{"fieldname": "kpi_period", "label": _("Period"), "fieldtype": "Link", "options": "CW KPI Period", "width": 100},
	]
	for category in shown:
		columns.append({"fieldname": frappe.scrub(category), "label": _(category), "fieldtype": "Percent", "width": 120})
	columns += [
		{"fieldname": "final_score", "label": _("Total"), "fieldtype": "Percent", "width": 90},
		{"fieldname": "reviews", "label": _("Monthly Reviews"), "fieldtype": "Data", "width": 110},
		{"fieldname": "eligibility", "label": _("Decision"), "fieldtype": "Data", "width": 110},
		{"fieldname": "eligibility_reasons", "label": _("Why"), "fieldtype": "Small Text", "width": 320},
	]

	data = []
	for evaluation in evaluations:
		row = dict(evaluation)
		row["reviews"] = f"{evaluation.months_reviewed or 0} / {evaluation.months_required or 0}"
		for category in shown:
			result = results.get(evaluation.name, {}).get(category)
			row[frappe.scrub(category)] = result.score if result and result.meets_minimum != "Not Measured" else None
		data.append(row)

	eligible = sum(1 for e in evaluations if e.eligibility == "Eligible")
	chart = {
		"data": {
			"labels": [_("Eligible"), _("Not Eligible"), _("Incomplete")],
			"datasets": [{"values": [eligible,
									 sum(1 for e in evaluations if e.eligibility == "Not Eligible"),
									 sum(1 for e in evaluations if e.eligibility == "Incomplete")]}],
		},
		"type": "donut",
		"colors": ["#27ae60", "#eb5757", "#f2994a"],
	}
	summary = [
		{"label": _("Evaluations"), "value": len(evaluations), "indicator": "blue"},
		{"label": _("Eligible"), "value": eligible, "indicator": "green"},
	]
	return columns, data, None, chart, summary
