# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

try:
	import frappe
	from frappe import _
	from frappe.model.document import Document
	from frappe.utils import flt
except ImportError:
	frappe = None  # type: ignore
	def _(msg): return msg
	def flt(v, precision=None):
		try: return float(v)
		except (ValueError, TypeError): return 0.0
	class Document:  # type: ignore
		pass


class CWEmployeeKPIPlan(Document):
	def validate(self):
		self.calculate_and_validate_weights()

	def calculate_and_validate_weights(self):
		total = sum(flt(item.weight) for item in getattr(self, "plan_items", []))
		self.total_weight = round(total, 2)

		if getattr(self, "plan_items", []) and round(total, 1) != 100.0:
			if frappe:
				frappe.throw(_("The sum of KPI weights must equal 100%. Current sum: {0}%").format(self.total_weight))


def get_permission_query_conditions(user):
	if not user or not frappe:
		return ""

	roles = frappe.get_roles(user)
	if "System Manager" in roles or "CW KPI Administrator" in roles or "CW Department Manager" in roles:
		return ""

	return f"""(`tabCW Employee KPI Plan`.employee IN (
		SELECT name FROM `tabEmployee` WHERE user_id = {frappe.db.escape(user)}
	))"""
