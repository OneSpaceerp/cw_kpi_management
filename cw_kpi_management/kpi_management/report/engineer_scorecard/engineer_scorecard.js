// Copyright (c) 2026, Nest Software Development & C-Water
// For license information, please see license.txt

frappe.query_reports["Engineer Scorecard"] = {
	filters: [
		{ fieldname: "kpi_period", label: __("Period"), fieldtype: "Link", options: "CW KPI Period" },
		{ fieldname: "department", label: __("Department"), fieldtype: "Link", options: "Department" },
		{ fieldname: "employee", label: __("Engineer"), fieldtype: "Link", options: "Employee" },
		{ fieldname: "eligibility", label: __("Decision"), fieldtype: "Select", options: "\nEligible\nNot Eligible\nIncomplete" },
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "eligibility" && data) {
			const color = { Eligible: "green", "Not Eligible": "red", Incomplete: "orange" }[data.eligibility];
			if (color) value = `<span class="indicator-pill ${color}">${value}</span>`;
		}
		return value;
	},
};
