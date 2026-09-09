# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

import unittest
from cw_kpi_management.kpi_management.doctype.cw_employee_kpi_plan.cw_employee_kpi_plan import CWEmployeeKPIPlan
from cw_kpi_management.kpi_management.doctype.cw_kpi_evaluation.cw_kpi_evaluation import CWKPIEvaluation


class DummyPlan(CWEmployeeKPIPlan):
	def __init__(self, **kwargs):
		self.__dict__.update(kwargs)


class DummyEvaluation(CWKPIEvaluation):
	def __init__(self, **kwargs):
		self.__dict__.update(kwargs)


class DummyPlanItem:
	def __init__(self, weight):
		self.weight = weight


class TestKPIEvaluation(unittest.TestCase):
	def test_plan_weight_sum_valid(self):
		plan = DummyPlan(
			plan_items=[
				DummyPlanItem(40.0),
				DummyPlanItem(30.0),
				DummyPlanItem(30.0),
			]
		)
		plan.calculate_and_validate_weights()
		self.assertEqual(plan.total_weight, 100.0)

	def test_grade_ratings(self):
		# Grade A
		eval_a = DummyEvaluation(final_score=92.5)
		eval_a.update_grade()
		self.assertEqual(eval_a.grade, "A - Outstanding (90-100%)")

		# Grade B
		eval_b = DummyEvaluation(final_score=84.0)
		eval_b.update_grade()
		self.assertEqual(eval_b.grade, "B - Exceeds Expectations (80-89%)")

		# Grade C
		eval_c = DummyEvaluation(final_score=75.0)
		eval_c.update_grade()
		self.assertEqual(eval_c.grade, "C - Meets Expectations (70-79%)")

		# Grade D
		eval_d = DummyEvaluation(final_score=62.0)
		eval_d.update_grade()
		self.assertEqual(eval_d.grade, "D - Below Expectations (60-69%)")

		# Grade F
		eval_f = DummyEvaluation(final_score=45.0)
		eval_f.update_grade()
		self.assertEqual(eval_f.grade, "F - Unsatisfactory (<60%)")


if __name__ == "__main__":
	unittest.main()
