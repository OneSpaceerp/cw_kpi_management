# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

try:
	import frappe
	from frappe.model.document import Document
except ImportError:
	class Document:  # type: ignore
		pass


class CWKPIPeriod(Document):
	def before_naming(self):
		if not self.period_name and self.start_date:
			self.period_name = suggest_name(self.period_type, self.start_date)

	def autoname(self):
		if not self.period_name and self.start_date:
			self.period_name = suggest_name(self.period_type, self.start_date)
		self.name = self.period_name

	def validate(self):
		if self.start_date and self.end_date:
			if self.start_date > self.end_date:
				if "frappe" in globals() and frappe:
					frappe.throw("Period Start Date cannot be later than End Date.")


def suggest_name(period_type, start_date) -> str:
	"""A period's name with its year, e.g. "Q1 2026", "October 2026", "H2 2026", "2026"."""
	from frappe.utils import getdate

	day = getdate(start_date)
	if period_type == "Quarterly":
		return f"Q{(day.month - 1) // 3 + 1} {day.year}"
	if period_type == "Monthly":
		return day.strftime("%B %Y")
	if period_type == "Semi-Annual":
		return f"H{1 if day.month <= 6 else 2} {day.year}"
	return str(day.year)

