// Copyright (c) 2026, Nest Software Development & C-Water
// For license information, please see license.txt

frappe.query_reports["KPI Payroll Reconciliation"] = {
	filters: [
		{
			fieldname: "kpi_period",
			label: __("KPI Period"),
			fieldtype: "Link",
			options: "CW KPI Period"
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department"
		},
		{
			fieldname: "compensation_type",
			label: __("Compensation Type"),
			fieldtype: "Select",
			options: "\nBonus\nCommission\nAllowance\nDeduction"
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nQueued for Payroll\nProcessed in Payroll\nCancelled"
		}
	]
};
