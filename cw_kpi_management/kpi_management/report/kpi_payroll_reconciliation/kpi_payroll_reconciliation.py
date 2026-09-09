# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

from typing import Any, Dict, List, Optional, Tuple

try:
	import frappe
except ImportError:
	frappe = None  # type: ignore


def execute(filters: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
	columns = [
		{"label": "Payroll Result ID", "fieldname": "name", "fieldtype": "Link", "options": "CW KPI Payroll Result", "width": 150},
		{"label": "Employee", "fieldname": "employee_name", "fieldtype": "Data", "width": 170},
		{"label": "Department", "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 140},
		{"label": "KPI Period", "fieldname": "kpi_period", "fieldtype": "Link", "options": "CW KPI Period", "width": 120},
		{"label": "Source Evaluation", "fieldname": "kpi_evaluation", "fieldtype": "Link", "options": "CW KPI Evaluation", "width": 150},
		{"label": "Score", "fieldname": "score", "fieldtype": "Float", "width": 90},
		{"label": "Type", "fieldname": "compensation_type", "fieldtype": "Data", "width": 110},
		{"label": "Salary Component", "fieldname": "salary_component", "fieldtype": "Link", "options": "Salary Component", "width": 150},
		{"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 130},
		{"label": "Additional Salary Doc", "fieldname": "additional_salary_doc", "fieldtype": "Link", "options": "Additional Salary", "width": 160},
	]

	if not frappe:
		return columns, []

	filters = filters or {}
	conds: Dict[str, Any] = {}
	if filters.get("kpi_period"):
		conds["kpi_period"] = filters["kpi_period"]
	if filters.get("department"):
		conds["department"] = filters["department"]
	if filters.get("compensation_type"):
		conds["compensation_type"] = filters["compensation_type"]
	if filters.get("status"):
		conds["status"] = filters["status"]

	results = frappe.get_all(
		"CW KPI Payroll Result",
		filters=conds,
		fields=[
			"name",
			"employee_name",
			"department",
			"kpi_period",
			"kpi_evaluation",
			"score",
			"compensation_type",
			"salary_component",
			"amount",
			"status",
			"additional_salary_doc",
		],
		order_by="creation desc",
	)

	return columns, results
