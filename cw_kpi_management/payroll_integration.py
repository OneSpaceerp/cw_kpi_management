# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

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


def on_evaluation_submit(doc, method=None):
	"""
	Triggered when a CW KPI Evaluation is approved and submitted.
	Evaluates matching compensation rules and generates CW KPI Payroll Result records.
	"""
	if not frappe:
		return

	generate_payroll_results_for_evaluation(doc.name)


def generate_payroll_results_for_evaluation(evaluation_name: str) -> List[str]:
	"""
	Matches evaluation against compensation rules and creates CW KPI Payroll Result.
	Returns list of created result document names.
	"""
	if not frappe:
		return []

	eval_doc = frappe.get_doc("CW KPI Evaluation", evaluation_name)
	score = flt(eval_doc.final_score or eval_doc.calculated_score)
	emp = eval_doc.employee

	# Fetch matching active compensation rules for employee's department
	rules = frappe.get_all(
		"CW KPI Compensation Rule",
		filters={
			"is_active": 1,
			"department": ["in", [eval_doc.department, ""]],
			"min_kpi_score": ["<=", score],
			"max_kpi_score": [">=", score],
		},
		fields=[
			"name",
			"rule_name",
			"compensation_type",
			"calculation_method",
			"amount_or_percent",
			"salary_component",
		],
	)

	created_results = []
	for rule in rules:
		# Compute monetary amount
		amount = 0.0
		if rule.calculation_method == "Fixed Amount":
			amount = flt(rule.amount_or_percent)
		elif rule.calculation_method == "Percentage of Base Salary":
			# Fetch base salary from employee's active salary structure assignment
			base_salary = frappe.db.get_value(
				"Salary Structure Assignment",
				{"employee": emp, "docstatus": 1},
				"base",
			) or 0.0
			amount = flt(base_salary) * (flt(rule.amount_or_percent) / 100.0)
		elif rule.calculation_method == "Graduated Scale":
			# Pro-rata based on score
			amount = flt(rule.amount_or_percent) * (score / 100.0)

		if amount <= 0.0:
			continue

		# Create CW KPI Payroll Result
		pay_res = frappe.get_doc({
			"doctype": "CW KPI Payroll Result",
			"employee": emp,
			"kpi_period": eval_doc.kpi_period,
			"kpi_evaluation": eval_doc.name,
			"compensation_rule": rule.name,
			"score": score,
			"compensation_type": rule.compensation_type,
			"salary_component": rule.salary_component,
			"amount": round(amount, 2),
			"status": "Queued for Payroll",
		})
		pay_res.insert(ignore_permissions=True)
		pay_res.submit()
		created_results.append(pay_res.name)

		# Push to standard ERPNext Additional Salary if Salary Component is linked
		if rule.salary_component:
			push_to_erpnext_additional_salary(pay_res)

	return created_results


def push_to_erpnext_additional_salary(payroll_result_doc) -> Optional[str]:
	"""
	Creates a standard ERPNext Additional Salary document from approved KPI Payroll Result.
	Safe, standard, upgrade-friendly integration.
	"""
	if not frappe:
		return None

	period_end = frappe.db.get_value("CW KPI Period", payroll_result_doc.kpi_period, "end_date") or now_datetime()

	# Check if Additional Salary DocType exists in this ERPNext installation
	if not frappe.db.exists("DocType", "Additional Salary"):
		frappe.logger("cw_kpi_management").warning("Additional Salary DocType not found; skipping automatic handoff.")
		return None

	add_sal = frappe.get_doc({
		"doctype": "Additional Salary",
		"employee": payroll_result_doc.employee,
		"salary_component": payroll_result_doc.salary_component,
		"amount": payroll_result_doc.amount,
		"payroll_date": period_end,
		"overwrite_salary_structure_amount": 0,
		"remarks": _("Generated from approved CW KPI Evaluation {0} (Score: {1})").format(
			payroll_result_doc.kpi_evaluation, payroll_result_doc.score
		),
	})
	add_sal.insert(ignore_permissions=True)
	add_sal.submit()

	# Update reference
	payroll_result_doc.status = "Processed in Payroll"
	payroll_result_doc.db_set("status", "Processed in Payroll")

	return add_sal.name
