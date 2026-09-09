// Copyright (c) 2026, Nest Software Development & C-Water
// For license information, please see license.txt

frappe.query_reports["Employee KPI Summary"] = {
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
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nDraft\nCalculated\nPending Manager Review\nPending Approval\nApproved\nRejected"
		}
	]
};
