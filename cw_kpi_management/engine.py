# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

from typing import Any, Dict, List, Optional, Tuple

try:
	import frappe
	from frappe.utils import flt, getdate
except ImportError:
	frappe = None  # type: ignore
	def flt(v, precision=None):
		try: return float(v)
		except (ValueError, TypeError): return 0.0
	def getdate(v): return v


class KPICalculationEngine:
	"""
	Deterministic server-side KPI calculation engine supporting 8 KPI types,
	directionality (Higher is Better, Lower is Better, Range is Best),
	floors, caps, score bounds, weighting, and full audit traces.
	"""

	@staticmethod
	def calculate_line_score(
		kpi_type: str,
		directionality: str,
		actual: float,
		target: float,
		weight: float = 0.0,
		min_score: float = 0.0,
		max_score: float = 100.0,
		cap_achievement_pct: Optional[float] = None,
		floor_achievement_pct: Optional[float] = None,
		threshold_value: Optional[float] = None,
		range_min: Optional[float] = None,
		range_max: Optional[float] = None,
	) -> Dict[str, Any]:
		"""
		Calculates raw achievement percentage, scaled score, and weighted score for a single KPI item.
		Returns detailed dictionary with audit trace.
		"""
		actual = flt(actual)
		target = flt(target)
		weight = flt(weight)
		trace: List[str] = []

		trace.append(f"Input: actual={actual}, target={target}, type={kpi_type}, direction={directionality}")

		# 1. Compute raw achievement percentage
		achievement_pct = 0.0

		if kpi_type in ["Target Achievement", "Count Target", "Percentage Target"]:
			if target == 0.0:
				achievement_pct = 100.0 if actual >= 0.0 else 0.0
				trace.append("Target is 0.0; defaulted achievement to 100% (or 0% if negative)")
			else:
				if directionality == "Higher is Better":
					achievement_pct = (actual / target) * 100.0
					trace.append(f"Higher is Better: ({actual} / {target}) * 100 = {achievement_pct:.2f}%")
				elif directionality == "Lower is Better":
					if actual <= 0.0:
						achievement_pct = 100.0
						trace.append("Lower is Better: actual <= 0; achieved 100%")
					else:
						# Scaled achievement: at target -> 100%, below target -> >100%, above target -> decreases
						achievement_pct = max(0.0, (2.0 - (actual / target)) * 100.0)
						trace.append(f"Lower is Better: max(0, 2 - ({actual}/{target})) * 100 = {achievement_pct:.2f}%")
				else:  # Range is Best
					achievement_pct = KPICalculationEngine._eval_range_achievement(actual, range_min or (target * 0.9), range_max or (target * 1.1), trace)

		elif kpi_type == "Threshold":
			t_val = flt(threshold_value) if threshold_value is not None else target
			if directionality == "Lower is Better":
				passed = actual <= t_val
				trace.append(f"Threshold (Lower is Better): {actual} <= {t_val} -> {'PASS' if passed else 'FAIL'}")
			else:
				passed = actual >= t_val
				trace.append(f"Threshold (Higher is Better): {actual} >= {t_val} -> {'PASS' if passed else 'FAIL'}")
			achievement_pct = 100.0 if passed else 0.0

		elif kpi_type == "Range-based":
			r_min = flt(range_min) if range_min is not None else (target * 0.9)
			r_max = flt(range_max) if range_max is not None else (target * 1.1)
			achievement_pct = KPICalculationEngine._eval_range_achievement(actual, r_min, r_max, trace)

		elif kpi_type in ["Attendance-derived", "Manual/Manager Rating", "Composite"]:
			# Direct percentage or score passed in actual
			achievement_pct = actual
			trace.append(f"Direct metric score applied: {achievement_pct:.2f}%")

		else:
			achievement_pct = (actual / target * 100.0) if target != 0 else 0.0
			trace.append(f"Generic metric achievement: {achievement_pct:.2f}%")

		# 2. Apply Floor constraint
		if floor_achievement_pct is not None and floor_achievement_pct > 0.0:
			if achievement_pct < floor_achievement_pct:
				trace.append(f"Achievement ({achievement_pct:.2f}%) below floor ({floor_achievement_pct}%); resetting to 0%")
				achievement_pct = 0.0

		# 3. Apply Cap constraint
		if cap_achievement_pct is not None and cap_achievement_pct > 0.0:
			if achievement_pct > cap_achievement_pct:
				trace.append(f"Achievement ({achievement_pct:.2f}%) capped at {cap_achievement_pct}%")
				achievement_pct = cap_achievement_pct

		# 4. Scale score to [min_score, max_score]
		score = max(min_score, min(max_score, achievement_pct))
		trace.append(f"Score bounded to [{min_score}, {max_score}]: {score:.2f}")

		# 5. Compute Weighted Score
		weighted_score = round(score * (weight / 100.0), 2)
		trace.append(f"Weighted Score: {score:.2f} * ({weight}% / 100) = {weighted_score:.2f}")

		return {
			"actual": round(actual, 2),
			"target": round(target, 2),
			"achievement_pct": round(achievement_pct, 2),
			"score": round(score, 2),
			"weight": round(weight, 2),
			"weighted_score": weighted_score,
			"trace": " | ".join(trace),
		}

	@staticmethod
	def _eval_range_achievement(actual: float, r_min: float, r_max: float, trace: List[str]) -> float:
		if r_min <= actual <= r_max:
			trace.append(f"Value {actual} is inside optimal range [{r_min}, {r_max}] -> 100%")
			return 100.0
		elif actual < r_min:
			dev = (r_min - actual) / r_min if r_min != 0 else 1.0
			res = max(0.0, (1.0 - dev) * 100.0)
			trace.append(f"Value {actual} is below optimal min {r_min} (dev {dev:.2f}) -> {res:.2f}%")
			return res
		else:
			dev = (actual - r_max) / r_max if r_max != 0 else 1.0
			res = max(0.0, (1.0 - dev) * 100.0)
			trace.append(f"Value {actual} is above optimal max {r_max} (dev {dev:.2f}) -> {res:.2f}%")
			return res

	@staticmethod
	def fetch_actual_from_erpnext(
		employee: str,
		data_source: str,
		start_date: str,
		end_date: str,
	) -> Tuple[float, str]:
		"""
		Fetches transactional actual metric value from standard ERPNext tables safely.
		"""
		if not frappe:
			return 0.0, "Frappe not available"

		user_id = frappe.db.get_value("Employee", employee, "user_id")

		if data_source == "CW Site Visits":
			# Count verified site visits completed by employee in the period
			cnt = frappe.db.count(
				"CW Site Visit",
				filters={
					"assigned_engineer": employee,
					"docstatus": 1,
					"planned_date": ["between", [start_date, end_date]],
				},
			)
			return float(cnt), f"Count of completed CW Site Visits: {cnt}"

		elif data_source == "ERPNext Attendance":
			# Calculate attendance percentage: (Present + Half Day*0.5) / Total Working Days * 100
			logs = frappe.get_all(
				"Attendance",
				filters={
					"employee": employee,
					"attendance_date": ["between", [start_date, end_date]],
					"docstatus": 1,
				},
				fields=["status"],
			)
			if not logs:
				return 100.0, "No attendance records found; defaulted to 100%"
			total = len(logs)
			present = sum(1 for l in logs if l.status == "Present")
			half = sum(0.5 for l in logs if l.status == "Half Day")
			pct = ((present + half) / total) * 100.0
			return round(pct, 2), f"Attendance {present + half}/{total} days ({pct:.1f}%)"

		elif data_source == "ERPNext Sales Invoices":
			# Total submitted sales invoice grand total for user/employee
			val = frappe.db.sql(
				"""
				SELECT COALESCE(SUM(base_grand_total), 0)
				FROM `tabSales Invoice`
				WHERE docstatus = 1
				  AND posting_date BETWEEN %s AND %s
				  AND (owner = %s OR customer IN (
				  	SELECT dl.link_name FROM `tabDynamic Link` dl
				  	WHERE dl.parent = %s AND dl.link_doctype = 'Customer'
				  ))
				""",
				(start_date, end_date, user_id or employee, employee),
			)[0][0]
			return float(val), f"Sales Invoice Total: {val}"

		elif data_source == "ERPNext Quotations":
			# Total approved quotations count
			cnt = frappe.db.count(
				"Quotation",
				filters={
					"docstatus": 1,
					"transaction_date": ["between", [start_date, end_date]],
					"owner": user_id or employee,
				},
			)
			return float(cnt), f"Quotation Count: {cnt}"

		return 0.0, "Manual or unmapped data source"
