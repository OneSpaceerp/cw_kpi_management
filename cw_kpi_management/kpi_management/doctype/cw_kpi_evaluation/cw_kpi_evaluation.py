# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

try:
	import frappe
	from frappe import _
	from frappe.model.document import Document
	from frappe.utils import flt, now_datetime
except ImportError:
	frappe = None  # type: ignore
	def _(msg): return msg
	class Document:  # type: ignore
		pass
	def flt(v, precision=None):
		try: return float(v)
		except (ValueError, TypeError): return 0.0
	def now_datetime():
		from datetime import datetime
		return datetime.now()


class CWKPIEvaluation(Document):
	def validate(self):
		self.update_grade()

	def update_grade(self):
		score = flt(self.final_score or self.calculated_score)
		if score >= 90.0:
			self.grade = "A - Outstanding (90-100%)"
		elif score >= 80.0:
			self.grade = "B - Exceeds Expectations (80-89%)"
		elif score >= 70.0:
			self.grade = "C - Meets Expectations (70-79%)"
		elif score >= 60.0:
			self.grade = "D - Below Expectations (60-69%)"
		else:
			self.grade = "F - Unsatisfactory (<60%)"

	def before_submit(self):
		if self.status != "Approved":
			if frappe:
				frappe.throw(_("Evaluation cannot be submitted until status is Approved by an authorized manager."))
		if not self.approver:
			if frappe:
				self.approver = frappe.session.user
		if not self.approval_timestamp:
			self.approval_timestamp = now_datetime()


def get_permission_query_conditions(user):
	if not user or not frappe:
		return ""

	roles = frappe.get_roles(user)
	if "System Manager" in roles or "CW KPI Administrator" in roles or "CW Department Manager" in roles:
		return ""

	return f"""(`tabCW KPI Evaluation`.employee IN (
		SELECT name FROM `tabEmployee` WHERE user_id = {frappe.db.escape(user)}
	))"""
