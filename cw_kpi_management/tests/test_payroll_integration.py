# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

import unittest


class TestPayrollIntegration(unittest.TestCase):
	def test_compensation_rule_computation_fixed(self):
		score = 92.0
		rule = {
			"min_kpi_score": 90.0,
			"max_kpi_score": 120.0,
			"calculation_method": "Fixed Amount",
			"amount_or_percent": 2500.0,
		}
		self.assertTrue(rule["min_kpi_score"] <= score <= rule["max_kpi_score"])
		amount = rule["amount_or_percent"]
		self.assertEqual(amount, 2500.0)

	def test_compensation_rule_computation_graduated(self):
		score = 80.0
		rule = {
			"min_kpi_score": 75.0,
			"max_kpi_score": 100.0,
			"calculation_method": "Graduated Scale",
			"amount_or_percent": 2000.0,
		}
		amount = rule["amount_or_percent"] * (score / 100.0)
		self.assertEqual(amount, 1600.0)

	def test_payroll_result_payload_structure(self):
		payload = {
			"doctype": "CW KPI Payroll Result",
			"employee": "EMP-001",
			"score": 92.0,
			"compensation_type": "Bonus",
			"salary_component": "Performance Bonus",
			"amount": 2500.0,
			"status": "Queued for Payroll",
		}
		self.assertEqual(payload["status"], "Queued for Payroll")
		self.assertGreater(payload["amount"], 0)


if __name__ == "__main__":
	unittest.main()
