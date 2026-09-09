// Copyright (c) 2026, Nest Software Development & C-Water
// For license information, please see license.txt

frappe.ui.form.on("CW KPI Evaluation", {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.docstatus === 0) {
			// Action button to calculate
			frm.add_custom_button(__("Calculate KPI Score"), function () {
				frappe.call({
					method: "cw_kpi_management.api.calculate_evaluation",
					args: { evaluation_name: frm.doc.name },
					callback: function (r) {
						if (r.message && r.message.status === "success") {
							frm.reload_doc();
							frappe.show_alert({ message: __("KPI calculation completed. Score: {0}", [r.message.calculated_score]), indicator: "green" });
						}
					}
				});
			}, __("Actions"));

			// Manual override button
			frm.add_custom_button(__("Apply Manual Override"), function () {
				let kpi_options = (frm.doc.evaluation_lines || []).map(l => ({ label: `${l.kpi_name} (${l.kpi_definition})`, value: l.kpi_definition }));
				frappe.prompt([
					{
						fieldname: "kpi_definition",
						label: __("Select KPI"),
						fieldtype: "Select",
						options: kpi_options,
						reqd: 1
					},
					{
						fieldname: "new_score",
						label: __("New Score (0-100)"),
						fieldtype: "Float",
						reqd: 1
					},
					{
						fieldname: "reason",
						label: __("Mandatory Justification Reason"),
						fieldtype: "Small Text",
						reqd: 1
					}
				], function (values) {
					frappe.call({
						method: "cw_kpi_management.api.apply_manual_override",
						args: {
							evaluation_name: frm.doc.name,
							kpi_definition: values.kpi_definition,
							new_score: values.new_score,
							reason: values.reason
						},
						callback: function (r) {
							if (r.message && r.message.status === "success") {
								frm.reload_doc();
								frappe.show_alert({ message: __("Override applied. New Total: {0}", [r.message.new_final_score]), indicator: "blue" });
							}
						}
					});
				}, __("Manual Score Adjustment"));
			}, __("Actions"));

			// Load lines from plan
			if (!frm.doc.evaluation_lines || frm.doc.evaluation_lines.length === 0) {
				frm.add_custom_button(__("Load Lines from Plan"), function () {
					frappe.call({
						method: "frappe.client.get",
						args: {
							doctype: "CW Employee KPI Plan",
							name: frm.doc.kpi_plan
						},
						callback: function (r) {
							if (r.message && r.message.plan_items) {
								frm.clear_table("evaluation_lines");
								r.message.plan_items.forEach(function (item) {
									let row = frm.add_child("evaluation_lines");
									row.kpi_definition = item.kpi_definition;
									row.kpi_name = item.kpi_name;
									row.target_value = item.target_value;
									row.actual_value = 0.0;
									row.weight = item.weight;
								});
								frm.refresh_field("evaluation_lines");
								frappe.show_alert({ message: __("Lines loaded from KPI Plan"), indicator: "green" });
							}
						}
					});
				}, __("Tools"));
			}
		}
	}
});
