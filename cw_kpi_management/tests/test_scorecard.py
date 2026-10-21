# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

"""The scorecard engine against C-Water's evaluation sheet (CWater_Engineers_KPI_Calculator.xlsx).

The sample engineer in the sheet scores 92.63% and is eligible. These tests reproduce that,
then check each gap the review of the sheet found.
"""

import unittest

from cw_kpi_management import scorecard as sc

CATEGORIES = [
	sc.Category("Maintenance", 40),
	sc.Category("Sales", 20),
	sc.Category("Kit & Tools", 15),
	sc.Category("Reports", 15),
	sc.Category("Appearance & Safety", 10),
]
CRITERIA = [
	sc.Criterion("MNT-01", "Maintenance", 30),
	sc.Criterion("MNT-02", "Maintenance", 25),
	sc.Criterion("MNT-03", "Maintenance", 25),
	sc.Criterion("MNT-04", "Maintenance", 20),
	sc.Criterion("SAL-01", "Sales", 50),
	sc.Criterion("SAL-02", "Sales", 25),
	sc.Criterion("SAL-03", "Sales", 25),
	sc.Criterion("KIT-01", "Kit & Tools", 40),
	sc.Criterion("KIT-02", "Kit & Tools", 40),
	sc.Criterion("KIT-03", "Kit & Tools", 20),
	sc.Criterion("REP-01", "Reports", 40),
	sc.Criterion("REP-02", "Reports", 30),
	sc.Criterion("REP-03", "Reports", 30),
	sc.Criterion("APP-01", "Appearance & Safety", 40),
	sc.Criterion("APP-02", "Appearance & Safety", 30),
	sc.Criterion("APP-03", "Appearance & Safety", 30),
]
# The sheet's sample: months 1 and 2 (month 3 empty).
MONTH_1 = {"MNT-01": 100, "MNT-02": 90, "MNT-03": 88, "MNT-04": 90, "SAL-01": 80, "SAL-02": 75, "SAL-03": 95,
		   "KIT-01": 100, "KIT-02": 90, "KIT-03": 90, "REP-01": 100, "REP-02": 90, "REP-03": 80,
		   "APP-01": 100, "APP-02": 100, "APP-03": 100}
MONTH_2 = {"MNT-01": 95, "MNT-02": 92, "MNT-03": 90, "MNT-04": 92, "SAL-01": 90, "SAL-02": 100, "SAL-03": 100,
		   "KIT-01": 95, "KIT-02": 100, "KIT-03": 90, "REP-01": 90, "REP-02": 90, "REP-03": 100,
		   "APP-01": 100, "APP-02": 90, "APP-03": 100}
MONTH_3 = dict(MONTH_2)


def rules(**overrides):
	return sc.Rules(**{"pass_total": 85, "min_category": 70, "months_required": 3, **overrides})


def by_key(result):
	return {c.key: c.score for c in result.categories}


class MatchesTheSheet(unittest.TestCase):
	def test_sample_engineer(self):
		result = sc.score_period(CATEGORIES, CRITERIA, [MONTH_1, MONTH_2], rules(months_required=2))
		self.assertEqual(
			by_key(result),
			{"Maintenance": 92.5, "Sales": 88.8, "Kit & Tools": 95.0, "Reports": 92.0, "Appearance & Safety": 98.5},
		)
		self.assertEqual(result.total, 92.6)  # the sheet: 92.63%
		self.assertEqual(result.decision, sc.ELIGIBLE)

	def test_monthly_scores(self):
		self.assertEqual(sc.score_month(CATEGORIES, CRITERIA, MONTH_1, rules()).total, 91.3)  # sheet 91.25%
		self.assertEqual(sc.score_month(CATEGORIES, CRITERIA, MONTH_2, rules()).total, 94.0)  # sheet 94.01%

	def test_a_category_under_70_fails_even_with_a_high_total(self):
		months = [{**MONTH_2, "SAL-01": 50, "SAL-02": 60, "SAL-03": 60}] * 3
		result = sc.score_period(CATEGORIES, CRITERIA, months, rules())
		self.assertGreaterEqual(result.total, 85)
		self.assertEqual(result.decision, sc.NOT_ELIGIBLE)
		self.assertTrue(any("Sales" in reason for reason in result.reasons))

	def test_total_under_85_fails(self):
		months = [{key: 80 for key in MONTH_1}] * 3
		result = sc.score_period(CATEGORIES, CRITERIA, months, rules())
		self.assertEqual(result.total, 80.0)
		self.assertEqual(result.decision, sc.NOT_ELIGIBLE)


class ClosesTheGaps(unittest.TestCase):
	def test_weights_inside_a_category_must_total_100(self):
		bad = [sc.Criterion(c.key, c.category, 35 if c.key == "MNT-01" else c.weight) for c in CRITERIA]
		with self.assertRaises(sc.ScorecardError):
			sc.validate(CATEGORIES, bad)

	def test_category_weights_must_total_100(self):
		with self.assertRaises(sc.ScorecardError):
			sc.validate([sc.Category(c.key, 25 if c.key == "Sales" else c.weight) for c in CATEGORIES], CRITERIA)

	def test_achievement_is_capped_at_100(self):
		pasted = {**MONTH_2, "SAL-01": 160}
		self.assertEqual(sc.score_month(CATEGORIES, CRITERIA, pasted, rules()).criteria["SAL-01"]["value"], 100.0)
		self.assertEqual(sc.clamp(-20), 0.0)

	def test_unmeasured_criterion_is_excluded_by_default(self):
		# The sheet scores a missing customer-satisfaction criterion as 0% (Maintenance 74.25%).
		months = [{**m, "MNT-04": None} for m in (MONTH_1, MONTH_2, MONTH_3)]
		excluded = sc.score_period(CATEGORIES, CRITERIA, months, rules())
		zero = sc.score_period(CATEGORIES, CRITERIA, months, rules(missing_policy=sc.MISSING_ZERO))
		self.assertFalse(excluded.criteria["MNT-04"]["measured"])
		self.assertEqual(by_key(excluded)["Maintenance"], 92.7)  # (30x96.67 + 25x91.33 + 25x89.33) / 80
		self.assertLess(by_key(zero)["Maintenance"], 75)  # the sheet's behaviour, on request

	def test_month_and_quarter_follow_the_same_rule(self):
		month = {**MONTH_1, "MNT-04": None}
		monthly = sc.score_month(CATEGORIES, CRITERIA, month, rules())
		quarter = sc.score_period(CATEGORIES, CRITERIA, [month], rules(months_required=1))
		self.assertEqual(by_key(monthly)["Maintenance"], by_key(quarter)["Maintenance"])

	def test_no_payment_decision_before_all_months_are_reviewed(self):
		result = sc.score_period(CATEGORIES, CRITERIA, [MONTH_1, MONTH_2], rules())
		self.assertEqual(result.decision, sc.INCOMPLETE)
		self.assertEqual(result.months_reviewed, 2)
		self.assertEqual(result.total, 92.6)  # the score is still shown

	def test_rounded_once_then_compared(self):
		# 84.96% shows as 85.0%, so it must pass as 85.0%.
		self.assertEqual(sc.rounded(84.96), 85.0)
		months = [{key: 84.96 for key in MONTH_1}] * 3
		self.assertEqual(sc.score_period(CATEGORIES, CRITERIA, months, rules()).decision, sc.ELIGIBLE)
		self.assertEqual(sc.rounded(88.65), 88.7)  # half up, not half to even

	def test_monthly_indicator_checks_category_minimums(self):
		month = {**MONTH_2, "KIT-01": 40, "KIT-02": 50, "KIT-03": 60}
		result = sc.score_month(CATEGORIES, CRITERIA, month, rules())
		self.assertGreaterEqual(result.total, 85)
		self.assertEqual(result.status, sc.NEEDS_IMPROVEMENT)
		self.assertTrue(any("Kit & Tools" in reason for reason in result.reasons))

	def test_nothing_measured(self):
		empty = {key: None for key in MONTH_1}
		self.assertEqual(sc.score_month(CATEGORIES, CRITERIA, empty, rules()).status, sc.NO_DATA)
		self.assertEqual(sc.score_period(CATEGORIES, CRITERIA, [empty] * 3, rules()).decision, sc.INCOMPLETE)

	def test_category_minimum_can_differ(self):
		cats = [sc.Category(c.key, c.weight, 95 if c.key == "Sales" else None) for c in CATEGORIES]
		result = sc.score_period(cats, CRITERIA, [MONTH_1, MONTH_2, MONTH_3], rules())
		sales = next(c for c in result.categories if c.key == "Sales")
		self.assertEqual((sales.score, sales.min_score, sales.meets_minimum), (90.8, 95, False))
		self.assertEqual(result.decision, sc.NOT_ELIGIBLE)

	def test_manager_override_replaces_the_period_value(self):
		result = sc.score_period(
			CATEGORIES, CRITERIA, [MONTH_1, MONTH_2, MONTH_3], rules(), overrides={"SAL-01": 100}
		)
		self.assertTrue(result.criteria["SAL-01"]["overridden"])
		self.assertEqual(result.criteria["SAL-01"]["value"], 100.0)


class SeededScorecard(unittest.TestCase):
	"""The scorecard installed on the site is the sheet's, and its weights are valid."""

	def load_seed(self):
		import importlib.util
		import pathlib
		import types

		sys_modules = __import__("sys").modules
		stub = sys_modules.setdefault("frappe", types.ModuleType("frappe"))
		path = pathlib.Path(__file__).resolve().parents[1] / "seed.py"
		spec = importlib.util.spec_from_file_location("cw_kpi_seed", path)
		module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(module)
		if stub.__dict__.get("__file__") is None:
			sys_modules.pop("frappe", None)
		return module

	def test_weights_match_the_sheet_and_validate(self):
		seed = self.load_seed()
		categories = [sc.Category(name, weight) for name, _ar, weight, _d in seed.CATEGORIES]
		criteria = [sc.Criterion(code, cat, weight) for code, _n, _ar, cat, weight, _s, _m in seed.CRITERIA]
		sc.validate(categories, criteria)
		self.assertEqual([c.weight for c in categories], [40, 20, 15, 15, 10])
		self.assertEqual(len(criteria), 16)


if __name__ == "__main__":
	unittest.main()
