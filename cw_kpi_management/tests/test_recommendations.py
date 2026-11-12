# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

import unittest

from cw_kpi_management.recommendations import recommend


def crit(code, category, weight, category_weight, achievement, source="Manual Entry", actual=None, required=None):
	return {
		"code": code,
		"name": code,
		"category": category,
		"weight": weight,
		"category_weight": category_weight,
		"achievement": achievement,
		"source": source,
		"actual": actual,
		"required": required,
	}


class Recommendations(unittest.TestCase):
	def test_ordered_by_points_to_gain(self):
		items = recommend(
			[
				crit("VISITS", "Maintenance", 30, 40, 75, "Visits: Plan Adherence", 6, 8),  # 0.4*0.3*25 = 3.0
				crit("UNIFORM", "Appearance", 40, 10, 50),  # 0.1*0.4*50 = 2.0
				crit("SALES", "Sales", 50, 20, 90, "Sales: Revenue vs Target", 90000, 100000),  # 1.0
			],
			[],
			{"total": 90, "pass_total": 85},
			{"days_left": 10, "planned_remaining": 3},
		)
		self.assertEqual([i.get("criterion") for i in items], ["VISITS", "UNIFORM", "SALES"])
		self.assertEqual(items[0]["impact"], 3.0)
		self.assertEqual(items[0]["params"]["missed"], 2)
		self.assertEqual(items[0]["params"]["planned_remaining"], 3)
		self.assertEqual(items[2]["params"]["per_day"], 1000.0)

	def test_thresholds_come_first(self):
		items = recommend(
			[crit("A", "Sales", 100, 20, 60)],
			[{"category": "Sales", "score": 60, "min_score": 70, "weight": 20}],
			{"total": 80, "pass_total": 85},
		)
		self.assertEqual([i["kind"] for i in items[:2]], ["total_gap", "category_minimum"])
		self.assertEqual(items[1]["params"]["gap"], 10)

	def test_full_marks_and_unmeasured(self):
		items = recommend(
			[crit("A", "M", 50, 100, 100), crit("B", "M", 50, 100, None)],
			[],
			{"total": 100, "pass_total": 85},
		)
		self.assertEqual(items[0]["kind"], "keep_going")
		self.assertEqual(items[-1]["kind"], "awaiting_review")
		self.assertEqual(items[-1]["params"]["count"], 1)

	def test_ask_for_feedback(self):
		items = recommend([], [], {"total": 95, "pass_total": 85}, {"visits_without_feedback": 4})
		self.assertTrue(any(i["kind"] == "ask_feedback" and i["params"]["count"] == 4 for i in items))

	def test_rating_in_stars(self):
		items = recommend(
			[crit("CSAT", "Maintenance", 20, 40, 76, "Visits: Customer Satisfaction", 76, 100)],
			[],
			{"total": 90, "pass_total": 85},
		)
		self.assertEqual(items[0]["params"]["stars"], 3.8)


class NothingMeasuredYet(unittest.TestCase):
	def test_not_called_on_track(self):
		items = recommend([crit("A", "M", 100, 100, None, "Visits: Plan Adherence")], [], {"total": None, "pass_total": 85})
		kinds = [i["kind"] for i in items]
		self.assertNotIn("keep_going", kinds)
		self.assertEqual(kinds[0], "nothing_measured")

	def test_open_visits_come_first(self):
		items = recommend([], [], {"total": None, "pass_total": 85}, {"open_visits": 4})
		self.assertEqual([i["kind"] for i in items[:2]], ["submit_open_visits", "nothing_measured"])
		self.assertEqual(items[0]["params"]["count"], 4)

	def test_open_visits_even_when_scoring_well(self):
		items = recommend([], [], {"total": 96, "pass_total": 85}, {"open_visits": 1})
		kinds = [i["kind"] for i in items]
		self.assertEqual(kinds[0], "submit_open_visits")
		self.assertNotIn("keep_going", kinds)


if __name__ == "__main__":
	unittest.main()
