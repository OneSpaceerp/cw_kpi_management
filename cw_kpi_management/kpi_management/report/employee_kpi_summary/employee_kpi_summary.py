# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

from typing import Any, Dict, List, Optional, Tuple

try:
	import frappe
except ImportError:
	frappe = None  # type: ignore


def execute(filters: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
	columns = [
		{"label": "Evaluation ID", "fieldname": "name", "fieldtype": "Link", "options": "CW KPI Evaluation", "width": 140},
		{"label": "Employee", "fieldname": "employee_name", "fieldtype": "Data", "width": 170},
		{"label": "Department", "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 140},
		{"label": "Designation", "fieldname": "designation", "fieldtype": "Link", "options": "Designation", "width": 140},
		{"label": "KPI Period", "fieldname": "kpi_period", "fieldtype": "Link", "options": "CW KPI Period", "width": 120},
		{"label": "Calculated Score", "fieldname": "calculated_score", "fieldtype": "Float", "width": 120},
		{"label": "Final Score", "fieldname": "final_score", "fieldtype": "Float", "width": 110},
		{"label": "Grade Rating", "fieldname": "grade", "fieldtype": "Data", "width": 160},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 110},
		{"label": "Approver", "fieldname": "approver", "fieldtype": "Link", "options": "User", "width": 140},
	]

	if not frappe:
		return columns, []

	filters = filters or {}
	conds: Dict[str, Any] = {}
	if filters.get("kpi_period"):
		conds["kpi_period"] = filters["kpi_period"]
	if filters.get("department"):
		conds["department"] = filters["department"]
	if filters.get("status"):
		conds["status"] = filters["status"]

	evals = frappe.get_all(
		"CW KPI Evaluation",
		filters=conds,
		fields=[
			"name",
			"employee_name",
			"department",
			"designation",
			"kpi_period",
			"calculated_score",
			"final_score",
			"grade",
			"status",
			"approver",
		],
		order_by="final_score desc",
	)

	return columns, evals
