// Copyright (c) 2026, Nest Software Development & C-Water
// For license information, please see license.txt

const CW_INDICATOR = { "On Track": "green", "Needs Improvement": "orange", "No Data": "gray" };

frappe.ui.form.on("CW KPI Monthly Review", {
	setup(frm) {
		frm.set_query("kpi_plan", () => ({
			filters: Object.assign({ status: "Active" }, frm.doc.employee ? { employee: frm.doc.employee } : {}),
		}));
	},

	refresh(frm) {
		if (!frm.is_new() && frm.doc.total_score !== undefined) {
			const color = CW_INDICATOR[frm.doc.monthly_indicator] || "gray";
			frm.dashboard.set_headline(
				`<span class="indicator-pill ${color}">${__(frm.doc.monthly_indicator || "No Data")}</span>
				 <b class="ml-2">${format_number(frm.doc.total_score || 0, null, 1)}%</b>
				 <span class="text-muted ml-2">${__("Monthly review only: no payment is made from it.")}</span>`
			);
		}
		if (frm.is_new() || frm.doc.docstatus !== 0) return;

		frm.add_custom_button(__("Fetch Data"), () =>
			frm.call("fetch_data").then(() => {
				frm.reload_doc();
				frappe.show_alert({ message: __("Visits, requests, feedback and sales refreshed"), indicator: "green" });
			})
		);
		frm.add_custom_button(
			__("Reload Criteria from Plan"),
			() =>
				frappe.confirm(__("Rebuild the criteria from the KPI plan? Entered values are cleared."), () =>
					frm.call("reload_criteria").then(() => frm.reload_doc())
				),
			__("Actions")
		);
	},

	employee(frm) {
		if (!frm.doc.employee) return;
		frappe.db
			.get_list("CW Employee KPI Plan", {
				filters: { employee: frm.doc.employee, status: "Active" },
				fields: ["name"],
				order_by: "creation desc",
				limit: 1,
			})
			.then((rows) => rows.length && !frm.doc.kpi_plan && frm.set_value("kpi_plan", rows[0].name));
	},
});

frappe.ui.form.on("CW KPI Monthly Review Line", {
	// Show the achievement as the manager types; the server recalculates on save.
	actual_value: (frm, cdt, cdn) => cw_line_achievement(frm, cdt, cdn),
	required_value: (frm, cdt, cdn) => cw_line_achievement(frm, cdt, cdn),
});

function cw_line_achievement(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	if (row.required_value > 0) {
		const value = Math.max(0, Math.min(100, ((row.actual_value || 0) / row.required_value) * 100));
		frappe.model.set_value(cdt, cdn, "achievement_percent", Math.round(value * 100) / 100);
	}
}
