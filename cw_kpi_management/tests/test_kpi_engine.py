# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

import unittest
from cw_kpi_management.engine import KPICalculationEngine


class TestKPICalculationEngine(unittest.TestCase):
	def test_higher_is_better_normal(self):
		# Target 100, Actual 80, Weight 50%
		res = KPICalculationEngine.calculate_line_score(
			kpi_type="Target Achievement",
			directionality="Higher is Better",
			actual=80.0,
			target=100.0,
			weight=50.0,
		)
		self.assertEqual(res["achievement_pct"], 80.0)
		self.assertEqual(res["score"], 80.0)
		self.assertEqual(res["weighted_score"], 40.0)

	def test_higher_is_better_overachievement_capped(self):
		# Target 100, Actual 150, Cap 120%, Weight 40%
		res = KPICalculationEngine.calculate_line_score(
			kpi_type="Target Achievement",
			directionality="Higher is Better",
			actual=150.0,
			target=100.0,
			weight=40.0,
			cap_achievement_pct=120.0,
		)
		self.assertEqual(res["achievement_pct"], 120.0)
		self.assertEqual(res["score"], 100.0)  # max_score default is 100.0
		self.assertEqual(res["weighted_score"], 40.0)

	def test_higher_is_better_floor_penalty(self):
		# Target 100, Actual 40, Floor 50%, Weight 50%
		res = KPICalculationEngine.calculate_line_score(
			kpi_type="Target Achievement",
			directionality="Higher is Better",
			actual=40.0,
			target=100.0,
			weight=50.0,
			floor_achievement_pct=50.0,
		)
		self.assertEqual(res["achievement_pct"], 0.0)
		self.assertEqual(res["score"], 0.0)
		self.assertEqual(res["weighted_score"], 0.0)

	def test_lower_is_better(self):
		# E.g. turnaround time or defect count: Target 10, Actual 8 (better than target)
		res = KPICalculationEngine.calculate_line_score(
			kpi_type="Count Target",
			directionality="Lower is Better",
			actual=8.0,
			target=10.0,
			weight=30.0,
		)
		# 2.0 - 0.8 = 1.2 -> 120%, capped at max_score 100
		self.assertEqual(res["achievement_pct"], 120.0)
		self.assertEqual(res["score"], 100.0)
		self.assertEqual(res["weighted_score"], 30.0)

	def test_threshold_pass_and_fail(self):
		# Pass test
		pass_res = KPICalculationEngine.calculate_line_score(
			kpi_type="Threshold",
			directionality="Higher is Better",
			actual=4.5,
			target=4.0,
			threshold_value=4.0,
			weight=20.0,
		)
		self.assertEqual(pass_res["score"], 100.0)
		self.assertEqual(pass_res["weighted_score"], 20.0)

		# Fail test
		fail_res = KPICalculationEngine.calculate_line_score(
			kpi_type="Threshold",
			directionality="Higher is Better",
			actual=3.8,
			target=4.0,
			threshold_value=4.0,
			weight=20.0,
		)
		self.assertEqual(fail_res["score"], 0.0)
		self.assertEqual(fail_res["weighted_score"], 0.0)

	def test_range_based_optimal(self):
		# Optimal range: 7.0 to 8.0 pH
		res = KPICalculationEngine.calculate_line_score(
			kpi_type="Range-based",
			directionality="Range is Best",
			actual=7.5,
			target=7.5,
			range_min=7.0,
			range_max=8.0,
			weight=25.0,
		)
		self.assertEqual(res["score"], 100.0)
		self.assertEqual(res["weighted_score"], 25.0)

	def test_attendance_and_manual_rating(self):
		res = KPICalculationEngine.calculate_line_score(
			kpi_type="Attendance-derived",
			directionality="Higher is Better",
			actual=94.5,
			target=100.0,
			weight=30.0,
		)
		self.assertEqual(res["score"], 94.5)
		self.assertEqual(res["weighted_score"], 28.35)


if __name__ == "__main__":
	unittest.main()
