# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

"""Two-level KPI scorecard: categories, each made of weighted criteria.

This is C-Water's engineer evaluation sheet (CWater_Engineers_KPI_Calculator.xlsx)
as code, with the gaps found in the sheet closed:

    the sheet                                     here
    -------------------------------------------   ------------------------------------------
    category weights checked, criterion weights    both levels must total 100% (validate)
    within a category not checked
    "capped at 100%" only by cell validation       every achievement is clamped to 0..cap
    a criterion with no data counts as 0%          explicit policy: exclude it and share its
                                                   weight among the measured criteria, or
                                                   count it as 0% (MISSING_* below)
    a month's category score treats a blank as 0,  months and the quarter use the same rule,
    the quarter leaves it out                      so they cannot disagree
    a decision with 1 or 2 of 3 months entered     fewer reviewed months than required gives
                                                   "Incomplete", never a payment decision
    84.96% shows as 85.0% and fails                scores are rounded once, then compared
    monthly "on track" ignores the 70% minimum     a month is on track only if the total and
                                                   every category meet their thresholds

Nothing here imports Frappe, so it is deterministic and unit-tested without a bench.
Scores are percentages (0-100). Weights are percentages too.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

MISSING_EXCLUDE = "Exclude and Reweight"
MISSING_ZERO = "Count as Zero"
MISSING_POLICIES = (MISSING_EXCLUDE, MISSING_ZERO)

ELIGIBLE = "Eligible"
NOT_ELIGIBLE = "Not Eligible"
INCOMPLETE = "Incomplete"

ON_TRACK = "On Track"
NEEDS_IMPROVEMENT = "Needs Improvement"
NO_DATA = "No Data"

WEIGHT_TOLERANCE = 0.01


class ScorecardError(ValueError):
	"""The scorecard's set-up is invalid (weights, categories)."""


@dataclass
class Category:
	key: str
	weight: float
	min_score: float | None = None  # None: the scorecard's default minimum
	label: str = ""


@dataclass
class Criterion:
	key: str
	category: str
	weight: float  # within its category
	cap: float = 100.0
	label: str = ""


@dataclass
class Rules:
	pass_total: float = 85.0
	min_category: float = 70.0
	missing_policy: str = MISSING_EXCLUDE
	months_required: int = 3
	precision: int = 1


@dataclass
class CategoryResult:
	key: str
	weight: float
	min_score: float
	score: float | None  # None when nothing in it was measured; rounded
	measured_weight: float  # how much of the category's weight was measured
	meets_minimum: bool | None
	raw: float | None = None  # unrounded, what the total is built from


@dataclass
class Result:
	criteria: dict = field(default_factory=dict)  # key -> {"value", "months_measured", "measured"}
	categories: list = field(default_factory=list)  # CategoryResult
	total: float | None = None
	months_reviewed: int = 0
	months_required: int = 0
	complete: bool = False
	decision: str = INCOMPLETE
	reasons: list = field(default_factory=list)
	status: str = NO_DATA  # monthly indicator for one month's result


# --------------------------------------------------------------------- set-up


def validate(categories: list[Category], criteria: list[Criterion]) -> None:
	"""Refuse a scorecard whose weights do not add up, at either level."""
	if not categories:
		raise ScorecardError("The scorecard has no categories.")
	keys = [c.key for c in categories]
	if len(keys) != len(set(keys)):
		raise ScorecardError("A category appears more than once.")

	total = sum(c.weight for c in categories)
	if abs(total - 100) > WEIGHT_TOLERANCE:
		raise ScorecardError(f"Category weights must total 100%. They total {total:g}%.")

	for category in categories:
		if category.weight < 0 or (category.min_score is not None and not 0 <= category.min_score <= 100):
			raise ScorecardError(f"Category {category.label or category.key}: weight or minimum out of range.")
		own = [c for c in criteria if c.category == category.key]
		if not own:
			raise ScorecardError(f"Category {category.label or category.key} has no criteria.")
		inner = sum(c.weight for c in own)
		if abs(inner - 100) > WEIGHT_TOLERANCE:
			raise ScorecardError(
				f"Criteria weights in {category.label or category.key} must total 100%. They total {inner:g}%."
			)

	stray = [c.label or c.key for c in criteria if c.category not in keys]
	if stray:
		raise ScorecardError("These criteria belong to no category of the scorecard: " + ", ".join(stray))


def clamp(value, cap: float = 100.0):
	"""An achievement as a number in 0..cap, or None when it is not a number (not measured)."""
	if value is None or value == "" or isinstance(value, bool):
		return None
	try:
		number = float(value)
	except (TypeError, ValueError):
		return None
	if number != number:  # NaN
		return None
	return max(0.0, min(float(cap or 100.0), number))


# ------------------------------------------------------------------- scoring


def score_categories(categories, criteria, values: dict, rules: Rules):
	"""Category scores and the total from one value per criterion (None = not measured)."""
	results = []
	anything_measured = any(values.get(c.key) is not None for c in criteria)
	for category in categories:
		own = [c for c in criteria if c.category == category.key]
		measured = [(c, values.get(c.key)) for c in own if values.get(c.key) is not None]
		minimum = rules.min_category if category.min_score is None else category.min_score

		if rules.missing_policy == MISSING_ZERO:
			# The sheet's own rule: what was not measured counts as 0%.
			score = sum(c.weight * (values.get(c.key) or 0.0) for c in own) / 100.0 if anything_measured else None
			measured_weight = sum(c.weight for c, _ in measured)
		else:
			measured_weight = sum(c.weight for c, _ in measured)
			score = sum(c.weight * v for c, v in measured) / measured_weight if measured_weight else None

		shown = rounded(score, rules.precision)
		results.append(
			CategoryResult(
				key=category.key,
				weight=category.weight,
				min_score=minimum,
				score=shown,
				measured_weight=round(measured_weight, 4),
				# Compared as shown, so a score displayed as 70.0% never fails a 70% minimum.
				meets_minimum=None if shown is None else shown >= minimum,
				raw=score,
			)
		)

	scored = [r for r in results if r.raw is not None]
	if not scored:
		return results, None
	if rules.missing_policy == MISSING_ZERO:
		total = sum(r.weight * (r.raw or 0.0) for r in results) / 100.0
	else:
		weight = sum(r.weight for r in scored)
		total = sum(r.weight * r.raw for r in scored) / weight
	return results, rounded(total, rules.precision)


def rounded(value, precision: int = 1):
	"""Half up, the way people round (Python's round() sends 88.65 to 88.6)."""
	if value is None:
		return None
	step = Decimal(1).scaleb(-int(precision))
	return float(Decimal(repr(value)).quantize(step, rounding=ROUND_HALF_UP))


def score_month(categories, criteria, entries: dict, rules: Rules) -> Result:
	"""One month: `entries` maps criterion key to the achievement entered (None = not measured).

	`status` is the monthly review indicator. It has no payment consequence.
	"""
	caps = {c.key: c.cap for c in criteria}
	values = {key: clamp(value, caps.get(key, 100.0)) for key, value in entries.items() if key in caps}
	category_results, total = score_categories(categories, criteria, values, rules)

	result = Result(
		criteria={c.key: {"value": values.get(c.key), "months_measured": int(values.get(c.key) is not None),
						  "measured": values.get(c.key) is not None} for c in criteria},
		categories=category_results,
		total=total,
		months_reviewed=1 if total is not None else 0,
		months_required=1,
		complete=total is not None,
	)
	result.reasons = _shortfalls(category_results, total, rules)
	if total is None:
		result.status = NO_DATA
	else:
		result.status = NEEDS_IMPROVEMENT if result.reasons else ON_TRACK
	return result


def score_period(categories, criteria, months: list[dict], rules: Rules, overrides: dict | None = None) -> Result:
	"""A whole period (a quarter) from its monthly reviews.

	`months` holds one `{criterion key: achievement or None}` per reviewed month. A
	criterion's value for the period is the average of the months it was measured in.
	`overrides` replaces a criterion's period value (an audited manager decision).
	"""
	validate(categories, criteria)
	if rules.missing_policy not in MISSING_POLICIES:
		raise ScorecardError(f"Unknown missing-data policy: {rules.missing_policy}")

	caps = {c.key: c.cap for c in criteria}
	criteria_values = {}
	for criterion in criteria:
		measured = [
			value
			for month in months
			if (value := clamp(month.get(criterion.key), caps[criterion.key])) is not None
		]
		criteria_values[criterion.key] = {
			"value": round(sum(measured) / len(measured), 4) if measured else None,
			"months_measured": len(measured),
			"measured": bool(measured),
			"overridden": False,
		}
	for key, value in (overrides or {}).items():
		if key in criteria_values:
			criteria_values[key].update(value=clamp(value, caps[key]), measured=clamp(value, caps[key]) is not None,
										overridden=True)

	values = {key: item["value"] for key, item in criteria_values.items()}
	category_results, total = score_categories(categories, criteria, values, rules)

	reviewed = sum(1 for month in months if any(v is not None for v in month.values()))
	result = Result(
		criteria=criteria_values,
		categories=category_results,
		total=total,
		months_reviewed=reviewed,
		months_required=max(int(rules.months_required or 0), 0),
	)
	result.complete = reviewed >= result.months_required and total is not None

	if not result.complete:
		result.decision = INCOMPLETE
		if total is None:
			result.reasons = ["Nothing was measured in this period."]
		else:
			result.reasons = [
				f"Only {reviewed} of {result.months_required} monthly reviews are submitted; "
				"no payment decision until all of them are."
			]
		return result

	result.reasons = _shortfalls(category_results, total, rules)
	result.decision = NOT_ELIGIBLE if result.reasons else ELIGIBLE
	if result.decision == ELIGIBLE:
		result.reasons = [
			f"Total {total:g}% meets {rules.pass_total:g}% and every category meets its minimum."
		]
	return result


def _shortfalls(category_results, total, rules: Rules) -> list[str]:
	reasons = []
	if total is not None and total < rules.pass_total:
		reasons.append(f"Total score {total:g}% is below {rules.pass_total:g}%.")
	for result in category_results:
		if result.meets_minimum is False:
			reasons.append(f"{result.key}: {result.score:g}% is below its minimum of {result.min_score:g}%.")
	return reasons
