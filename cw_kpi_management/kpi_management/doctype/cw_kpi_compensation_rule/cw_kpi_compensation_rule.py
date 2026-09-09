# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

try:
	import frappe
	from frappe.model.document import Document
except ImportError:
	class Document:  # type: ignore
		pass


class CWKPICompensationRule(Document):
	def validate(self):
		if self.min_kpi_score and self.max_kpi_score:
			if self.min_kpi_score > self.max_kpi_score:
				if "frappe" in globals() and frappe:
					frappe.throw("Min KPI Score cannot be greater than Max KPI Score.")
