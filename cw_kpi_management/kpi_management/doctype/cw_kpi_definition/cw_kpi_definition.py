# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

try:
	import frappe
	from frappe.model.document import Document
except ImportError:
	class Document:  # type: ignore
		pass


class CWKPIDefinition(Document):
	def validate(self):
		if self.range_min_value and self.range_max_value:
			if self.range_min_value > self.range_max_value:
				if "frappe" in globals() and frappe:
					frappe.throw("Range Min Value cannot exceed Range Max Value.")
