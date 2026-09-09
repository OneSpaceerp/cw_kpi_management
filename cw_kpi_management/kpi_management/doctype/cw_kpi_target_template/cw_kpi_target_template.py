# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

try:
	import frappe
	from frappe.model.document import Document
except ImportError:
	class Document:  # type: ignore
		pass


class CWKPITargetTemplate(Document):
	def validate(self):
		# Validate that weights sum to 100%
		total_weight = sum(item.weight for item in getattr(self, "template_items", []))
		if getattr(self, "template_items", []) and round(total_weight, 1) != 100.0:
			if "frappe" in globals() and frappe:
				frappe.throw(f"Total template weight must equal 100%. Current sum: {total_weight}%")
