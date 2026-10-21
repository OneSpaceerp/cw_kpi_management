// Copyright (c) 2026, Nest Software Development & C-Water
// For license information, please see license.txt

frappe.ui.form.on("CW Employee KPI Plan", {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.status === "Active" && (frm.doc.categories || []).length) {
			frm.add_custom_button(__("Monthly Review"), () => {
				frappe.prompt(
					[{ fieldname: "month", label: __("Month (any day of it)"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() }],
					(values) =>
						frappe
							.xcall("cw_kpi_management.api.create_monthly_review", { kpi_plan: frm.doc.name, month: values.month })
							.then((name) => frappe.set_route("Form", "CW KPI Monthly Review", name)),
					__("Monthly Review"),
					__("Open")
				);
			}, __("Actions"));
			frm.add_custom_button(__("Monthly Reviews"), () =>
				frappe.set_route("List", "CW KPI Monthly Review", { kpi_plan: frm.doc.name })
			, __("View"));
		}
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
						// The scorecard: categories and thresholds come with the criteria.
						["evaluation_cycle", "months_required", "missing_data_policy", "pass_total_score", "min_category_score"].forEach(
							(field) => r.message[field] !== undefined && frm.set_value(field, r.message[field])
						);
						frm.clear_table("categories");
						(r.message.categories || []).forEach((cat) => {
							const row = frm.add_child("categories");
							row.kpi_category = cat.kpi_category;
							row.weight = cat.weight;
							row.min_score = cat.min_score;
						});
						frm.refresh_field("categories");
						frm.clear_table("plan_items");
						r.message.template_items.forEach(function (item) {
							let row = frm.add_child("plan_items");
							row.kpi_definition = item.kpi_definition;
							row.kpi_name = item.kpi_name;
							row.kpi_category = item.kpi_category;
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
		if ((frm.doc.categories || []).length) return; // a scorecard is checked per category on save
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
