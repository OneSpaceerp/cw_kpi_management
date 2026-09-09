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


class CWKPIPayrollResult(Document):
	def validate(self):
		if flt(self.amount) <= 0:
			if frappe:
				frappe.throw(_("Approved Amount must be greater than zero."))

	def on_submit(self):
		if self.status == "Queued for Payroll" and frappe:
			from cw_kpi_management.payroll_integration import push_to_erpnext_additional_salary
			add_sal = push_to_erpnext_additional_salary(self)
			if add_sal:
				self.additional_salary_doc = add_sal
				self.db_set("additional_salary_doc", add_sal)
