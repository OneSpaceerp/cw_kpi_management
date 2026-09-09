// Copyright (c) 2026, Nest Software Development & C-Water
// For license information, please see license.txt

frappe.ui.form.on("CW KPI Payroll Result", {
	refresh(frm) {
		if (frm.doc.additional_salary_doc) {
			frm.add_custom_button(__("View Additional Salary"), function () {
				frappe.set_route("Form", "Additional Salary", frm.doc.additional_salary_doc);
			});
		}
	}
});
