# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

"""Where a criterion's monthly achievement comes from.

`measure(data_source, employee, start, end, target)` returns
`{"actual", "required", "note"}`. A required of 0 means nothing was required in the
month, which the scorecard treats as "not measured", never as 0%.

    Visits: ... / Service Requests: ...   the Visits app (cw_visit.kpi), when installed
    Sales: ...                             the Sales Person linked to the employee
                                           (Sales Person > Employee); the target is the
                                           plan line's target per month
    Manual Entry                           nothing to fetch; the manager enters it
"""

import frappe
from frappe import _
from frappe.utils import flt

VISIT_METRICS = {
	"Visits: Plan Adherence": "plan_adherence",
	"Service Requests: Response Within SLA": "response_within_sla",
	"Service Requests: Closed On Time": "closed_on_time",
	"Visits: Reports On Time": "reports_on_time",
	"Visits: Customer Satisfaction": "customer_satisfaction",
}
SALES_SOURCES = (
	"Sales: Revenue vs Target",
	"Sales: New Customers vs Target",
	"Sales: Quotations vs Target",
)
MANUAL = "Manual Entry"


def is_automatic(data_source: str | None) -> bool:
	return bool(data_source) and data_source in (*VISIT_METRICS, *SALES_SOURCES)


def measure(data_source: str, employee: str, start, end, target: float = 0) -> dict:
	if data_source in VISIT_METRICS:
		return _visit_metric(VISIT_METRICS[data_source], employee, start, end)
	if data_source in SALES_SOURCES:
		return _sales_metric(data_source, employee, start, end, flt(target))
	return {"actual": None, "required": None, "note": _("Entered by the manager")}


def _visit_metric(metric, employee, start, end):
	if "cw_visit" not in frappe.get_installed_apps():
		return {"actual": 0, "required": 0, "note": _("The Visits app is not installed")}
	result = frappe.get_attr("cw_visit.kpi.engineer_metric")(metric, employee, start, end)
	return {"actual": result["numerator"], "required": result["denominator"], "note": result["note"]}


def _sales_persons(employee) -> list:
	return frappe.get_all("Sales Person", filters={"employee": employee, "enabled": 1}, pluck="name")


def _sales_metric(source, employee, start, end, target):
	if target <= 0:
		return {"actual": 0, "required": 0, "note": _("No target set on the KPI plan for this criterion")}

	persons = _sales_persons(employee)
	user = frappe.db.get_value("Employee", employee, "user_id")
	if not persons and not user:
		return {"actual": 0, "required": target, "note": _("No Sales Person or user is linked to this employee")}

	if source == "Sales: Revenue vs Target":
		actual = _invoiced(persons, user, start, end)
		note = _("Invoiced {0} of a {1} target").format(frappe.format(actual, "Currency"), frappe.format(target, "Currency"))
	elif source == "Sales: New Customers vs Target":
		actual = _new_customers(persons, user, start, end)
		note = _("{0} new customer(s) of {1}").format(int(actual), int(target))
	else:
		actual = _quotations(persons, user, start, end)
		note = _("{0} quotation(s) submitted of {1}").format(int(actual), int(target))
	return {"actual": actual, "required": target, "note": note}


def _invoiced(persons, user, start, end) -> float:
	"""Net sales credited to the engineer: their Sales Team share, else invoices they raised."""
	if persons:
		return flt(
			frappe.db.sql(
				"""
				SELECT COALESCE(SUM(st.allocated_amount), 0)
				FROM `tabSales Team` st
				JOIN `tabSales Invoice` si ON si.name = st.parent
				WHERE st.parenttype = 'Sales Invoice' AND si.docstatus = 1 AND si.is_return = 0
				  AND si.posting_date BETWEEN %s AND %s AND st.sales_person IN %s
				""",
				(start, end, tuple(persons)),
			)[0][0]
		)
	return flt(
		frappe.db.sql(
			"""SELECT COALESCE(SUM(base_net_total), 0) FROM `tabSales Invoice`
			WHERE docstatus = 1 AND is_return = 0 AND posting_date BETWEEN %s AND %s AND owner = %s""",
			(start, end, user),
		)[0][0]
	)


def _new_customers(persons, user, start, end) -> float:
	filters = {"creation": ["between", [f"{start} 00:00:00", f"{end} 23:59:59"]]}
	names = set()
	if user:
		names |= set(frappe.get_all("Customer", filters={**filters, "owner": user}, pluck="name"))
	if persons:
		names |= set(
			frappe.get_all(
				"Sales Team",
				filters={"parenttype": "Customer", "sales_person": ["in", persons], "creation": filters["creation"]},
				pluck="parent",
			)
		)
	return float(len(names))


def _quotations(persons, user, start, end) -> float:
	filters = {"docstatus": 1, "transaction_date": ["between", [start, end]]}
	names = set()
	if user:
		names |= set(frappe.get_all("Quotation", filters={**filters, "owner": user}, pluck="name"))
	if persons:
		quoted = frappe.get_all(
			"Sales Team", filters={"parenttype": "Quotation", "sales_person": ["in", persons]}, pluck="parent"
		)
		if quoted:
			names |= set(frappe.get_all("Quotation", filters={**filters, "name": ["in", quoted]}, pluck="name"))
	return float(len(names))
