# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

"""One engineer, one month: the achievement of every criterion of their scorecard.

The manager reviews it with the engineer each month to correct course early. A monthly
review never triggers a payment; the quarterly CW KPI Evaluation averages the submitted
monthly reviews of the quarter and decides eligibility.

Criteria with an automatic data source (visits, service requests, customer feedback,
sales) are filled in by "Fetch Data"; the others are entered by the manager.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, formatdate, getdate

from cw_kpi_management import scorecard as sc
from cw_kpi_management import scorecard_service as service


class CWKPIMonthlyReview(Document):
	def validate(self):
		self.month_start, self.month_end = service.month_bounds(self.month_start)
		self.validate_plan()
		self.validate_one_per_month()
		if not self.lines:
			service.build_lines(self)
		if not self.reviewer:
			self.reviewer = frappe.session.user
		self.calculate()

	def before_submit(self):
		missing = [
			line.kpi_name or line.kpi_definition
			for line in self.lines
			if line.entry_mode == "Manual"
			and not cint(line.not_measured)
			and not flt(line.required_value)
			and not flt(line.actual_value)
			and not flt(line.achievement_percent)
		]
		if missing:
			frappe.throw(
				_(
					"Enter the achievement of these criteria, or tick Not Measured if nothing was required this month. "
					"For a real 0%, enter Achieved 0 and the Required amount."
				)
				+ "<br><br>"
				+ "<br>".join(frappe.utils.escape_html(name) for name in missing),
				title=_("Criteria not filled in"),
			)

	def validate_plan(self):
		plan = frappe.get_cached_doc("CW Employee KPI Plan", self.kpi_plan)
		if plan.employee != self.employee:
			frappe.throw(_("KPI Plan {0} belongs to another employee.").format(self.kpi_plan))
		if not service.has_scorecard(plan):
			frappe.throw(
				_("KPI Plan {0} has no scorecard categories. Monthly reviews need a scorecard plan.").format(self.kpi_plan)
			)
		if plan.kpi_period:
			period = frappe.get_cached_value("CW KPI Period", plan.kpi_period, ["start_date", "end_date"], as_dict=True)
			if period and period.start_date and not (
				getdate(period.start_date) <= getdate(self.month_start) <= getdate(period.end_date)
			):
				frappe.throw(
					_("{0} is outside the plan's period {1}.").format(formatdate(self.month_start, "MMMM yyyy"), plan.kpi_period)
				)

	def validate_one_per_month(self):
		other = frappe.db.get_value(
			"CW KPI Monthly Review",
			{
				"employee": self.employee,
				"month_start": self.month_start,
				"docstatus": ["<", 2],
				"name": ["!=", self.name or ""],
			},
			"name",
		)
		if other:
			frappe.throw(
				_("{0} already has a monthly review for {1}: {2}").format(
					self.employee_name or self.employee, formatdate(self.month_start, "MMMM yyyy"), other
				)
			)

	def calculate(self):
		plan = frappe.get_cached_doc("CW Employee KPI Plan", self.kpi_plan)
		categories, criteria = service.structure_of(plan)
		rules = service.rules_of(plan)

		entries = {}
		for line in self.lines:
			value = service.line_value(line)
			if not cint(line.not_measured) and flt(line.required_value) > 0:
				line.achievement_percent = value
			entries[line.kpi_definition] = value

		result = sc.score_month(categories, criteria, entries, rules)
		self.total_score = result.total or 0
		self.monthly_indicator = result.status
		self.indicator_reasons = "\n".join(result.reasons)
		self.set("category_results", service.category_rows(result))

	@frappe.whitelist()
	def fetch_data(self):
		"""Refresh the automatic criteria from visits, requests, feedback and sales."""
		self.check_permission("write")
		if self.docstatus != 0:
			frappe.throw(_("A submitted monthly review cannot change."))
		if not self.lines:
			service.build_lines(self)
		else:
			service.refresh_automatic_lines(self)
		self.save()
		return {"total_score": self.total_score, "monthly_indicator": self.monthly_indicator}

	@frappe.whitelist()
	def reload_criteria(self):
		"""Rebuild the lines from the plan, e.g. after the plan's criteria changed."""
		self.check_permission("write")
		if self.docstatus != 0:
			frappe.throw(_("A submitted monthly review cannot change."))
		service.build_lines(self)
		self.save()


def get_permission_query_conditions(user):
	if not user:
		return ""
	roles = frappe.get_roles(user)
	if {"System Manager", "CW KPI Administrator", "CW Department Manager"} & set(roles):
		return ""
	return f"""(`tabCW KPI Monthly Review`.employee IN (
		SELECT name FROM `tabEmployee` WHERE user_id = {frappe.db.escape(user)}
	))"""
