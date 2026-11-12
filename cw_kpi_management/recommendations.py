# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

"""What an engineer can do to raise their score, ordered by how much it would raise it.

Each recommendation is data, not text: a `kind` and the numbers behind it. The phone app
words it in the engineer's language. `impact` is the number of points the total would
gain if that criterion reached 100%, so the first recommendation is the one worth most.

Nothing here imports Frappe; it is unit-tested without a bench.
"""

from __future__ import annotations

SOURCE_KINDS = {
	"Visits: Plan Adherence": "visits_pending",
	"Service Requests: Response Within SLA": "respond_faster",
	"Service Requests: Closed On Time": "close_on_time",
	"Visits: Reports On Time": "reports_on_time",
	"Visits: Customer Satisfaction": "customer_rating",
	"Sales: Revenue vs Target": "sales_gap",
	"Sales: New Customers vs Target": "customers_gap",
	"Sales: Quotations vs Target": "quotations_gap",
}
FULL = 100.0
NEAR_FULL = 99.95


def recommend(criteria: list[dict], categories: list[dict], rules: dict, context: dict | None = None) -> list[dict]:
	"""`criteria`: {code, name, category, weight, category_weight, achievement, source, actual, required}
	(achievement None = not measured). `categories`: {category, score, min_score, weight}.
	`rules`: {pass_total, total}. `context`: {days_left, planned_remaining, visits_without_feedback}.
	"""
	context = context or {}
	items = []

	for category in categories:
		score, minimum = category.get("score"), category.get("min_score")
		if score is not None and minimum is not None and score < minimum:
			items.append(
				{
					"kind": "category_minimum",
					"category": category["category"],
					"impact": round(category.get("weight", 0) / 100 * (minimum - score), 2),
					"priority": True,
					"params": {"score": score, "min": minimum, "gap": round(minimum - score, 1)},
				}
			)

	total, pass_total = rules.get("total"), rules.get("pass_total")
	if total is not None and pass_total is not None and total < pass_total:
		items.append(
			{
				"kind": "total_gap",
				"impact": round(pass_total - total, 2),
				"priority": True,
				"params": {"total": total, "pass": pass_total, "gap": round(pass_total - total, 1)},
			}
		)

	awaiting = []
	for criterion in criteria:
		achievement = criterion.get("achievement")
		if achievement is None:
			if criterion.get("source") in (None, "", "Manual Entry"):
				awaiting.append(criterion["name"])
			continue
		if achievement >= NEAR_FULL:
			continue
		impact = criterion.get("category_weight", 0) / 100 * criterion.get("weight", 0) / 100 * (FULL - achievement)
		kind = SOURCE_KINDS.get(criterion.get("source"), "improve_criterion")
		items.append(
			{
				"kind": kind,
				"criterion": criterion["code"],
				"criterion_name": criterion["name"],
				"category": criterion["category"],
				"impact": round(impact, 2),
				"priority": False,
				"params": _params(kind, criterion, context),
			}
		)

	without = int(context.get("visits_without_feedback") or 0)
	if without:
		items.append(
			{
				"kind": "ask_feedback",
				"impact": 0,
				"priority": False,
				"params": {"count": without},
			}
		)
	if awaiting:
		items.append(
			{
				"kind": "awaiting_review",
				"impact": 0,
				"priority": False,
				"params": {"count": len(awaiting), "criteria": awaiting},
			}
		)

	items.sort(key=lambda item: (not item["priority"], -item["impact"]))
	if not any(item["impact"] > 0 for item in items):
		items.insert(0, {"kind": "keep_going", "impact": 0, "priority": False, "params": {"total": total}})
	return items


def _params(kind, criterion, context):
	actual = criterion.get("actual")
	required = criterion.get("required")
	achievement = round(criterion["achievement"], 1)
	params = {"achievement": achievement, "actual": actual, "required": required}

	if kind == "visits_pending":
		params["missed"] = max(0, int((required or 0) - (actual or 0)))
		params["planned_remaining"] = int(context.get("planned_remaining") or 0)
	elif kind in ("respond_faster", "close_on_time", "reports_on_time"):
		params["missed"] = max(0, int((required or 0) - (actual or 0)))
	elif kind == "customer_rating":
		params["stars"] = round(achievement / 20, 1)
	elif kind in ("sales_gap", "customers_gap", "quotations_gap"):
		remaining = max(0.0, (required or 0) - (actual or 0))
		days_left = max(int(context.get("days_left") or 0), 0)
		params["remaining"] = round(remaining, 2)
		params["days_left"] = days_left
		params["per_day"] = round(remaining / days_left, 2) if days_left else round(remaining, 2)
	return params
