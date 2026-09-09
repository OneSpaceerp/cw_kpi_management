// Copyright (c) 2026, Nest Software Development & C-Water
// For license information, please see license.txt

frappe.ui.form.on("CW Employee KPI Plan", {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.status === "Active") {
			frm.add_custom_button(__("Create Evaluation"), function () {
				frappe.new_doc("CW KPI Evaluation", {
					employee: frm.doc.employee,
					kpi_period: frm.doc.kpi_period,
					kpi_plan: frm.doc.name
				});
			}, __("Actions"));
		}
	},

	target_template(frm) {
		if (frm.doc.target_template) {
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "CW KPI Target Template",
					name: frm.doc.target_template
				},
				callback: function (r) {
					if (r.message && r.message.template_items) {
						frm.clear_table("plan_items");
						r.message.template_items.forEach(function (item) {
							let row = frm.add_child("plan_items");
							row.kpi_definition = item.kpi_definition;
							row.kpi_name = item.kpi_name;
							row.target_value = item.target_value;
							row.weight = item.weight;
							row.min_threshold = item.min_threshold;
							row.max_threshold = item.max_threshold;
						});
						frm.refresh_field("plan_items");
						frm.trigger("calculate_total_weight");
					}
				}
			});
		}
	},

	calculate_total_weight(frm) {
		let total = 0;
		(frm.doc.plan_items || []).forEach(function (row) {
			total += (row.weight || 0);
		});
		frm.set_value("total_weight", Math.round(total * 100) / 100);
	}
});

frappe.ui.form.on("CW Employee KPI Plan Item", {
	weight(frm) {
		frm.trigger("calculate_total_weight");
	},
	plan_items_remove(frm) {
		frm.trigger("calculate_total_weight");
	}
});
