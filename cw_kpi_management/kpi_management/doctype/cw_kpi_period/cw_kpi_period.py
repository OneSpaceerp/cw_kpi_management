# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

try:
	import frappe
	from frappe.model.document import Document
except ImportError:
	class Document:  # type: ignore
		pass


class CWKPIPeriod(Document):
	def validate(self):
		if self.start_date and self.end_date:
			if self.start_date > self.end_date:
				if "frappe" in globals() and frappe:
					frappe.throw("Period Start Date cannot be later than End Date.")
