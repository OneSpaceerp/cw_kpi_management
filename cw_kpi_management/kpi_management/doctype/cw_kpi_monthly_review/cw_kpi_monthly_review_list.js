// Copyright (c) 2026, Nest Software Development & C-Water
// For license information, please see license.txt

frappe.listview_settings["CW KPI Monthly Review"] = {
	add_fields: ["monthly_indicator", "total_score", "docstatus"],
	get_indicator(doc) {
		if (doc.docstatus === 2) return [__("Cancelled"), "red", "docstatus,=,2"];
		const colors = { "On Track": "green", "Needs Improvement": "orange", "No Data": "gray" };
		const label = doc.docstatus === 0 ? __("Draft") + " · " + __(doc.monthly_indicator) : __(doc.monthly_indicator);
		return [label, colors[doc.monthly_indicator] || "gray", `monthly_indicator,=,${doc.monthly_indicator}`];
	},
};
