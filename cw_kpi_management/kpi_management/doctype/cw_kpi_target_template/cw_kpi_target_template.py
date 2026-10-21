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
		if getattr(self, "categories", None):
			# Scorecard: category weights total 100%, and so do the criteria inside each category.
			from cw_kpi_management.scorecard_service import validate_structure

			validate_structure(self)
			return
		# Flat template: the KPI weights total 100%
		total_weight = sum(item.weight for item in getattr(self, "template_items", []))
		if getattr(self, "template_items", []) and round(total_weight, 1) != 100.0:
			if "frappe" in globals() and frappe:
				frappe.throw(f"Total template weight must equal 100%. Current sum: {total_weight}%")
