# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

"""C-Water's engineer scorecard, as defined in CWater_Engineers_KPI_Calculator.xlsx.

Inserted once, never overwritten: what C-Water tunes on the site (weights, minimums,
targets) survives every migrate. The weights, thresholds and measurement methods are the
sheet's own; nothing here is invented.
"""

import frappe

TEMPLATE = "C-Water Engineer Scorecard"

# (name, arabic name, weight, what is measured)
CATEGORIES = [
	("Maintenance", "الصيانة", 40, "Periodic visit plan, fault response, tickets closed on time, customer satisfaction"),
	("Sales", "المبيعات", 20, "Sales target, new customers, visits and technical offers"),
	("Kit & Tools Readiness", "جاهزية شنطة الأجهزة والأدوات", 15, "Complete kit, valid and calibrated instruments, supplies available"),
	("Reports to Management", "تقديم التقارير للإدارة", 15, "Visit, technical and sales reports, on time and complete"),
	("Appearance & Safety", "المظهر العام والسلامة", 10, "Uniform, vest, safety equipment"),
]

# (code, name, arabic name, category, weight in category, data source, how it is measured)
CRITERIA = [
	("CW-MNT-01", "Periodic Visit Plan Adherence", "الالتزام بجدول الزيارات الدورية", "Maintenance", 30,
	 "Visits: Plan Adherence", "Visits executed ÷ visits planned (زيارات منفذة ÷ زيارات مخططة)"),
	("CW-MNT-02", "Fault Response Time", "زمن الاستجابة للأعطال", "Maintenance", 25,
	 "Service Requests: Response Within SLA", "Faults answered within the SLA ÷ all faults due (أعطال تمت الاستجابة لها في المدة المحددة ÷ إجمالي الأعطال)"),
	("CW-MNT-03", "Tickets Closed On Time", "إغلاق التذاكر في موعدها", "Maintenance", 25,
	 "Service Requests: Closed On Time", "Tickets closed by their deadline ÷ all tickets due (تذاكر أُغلقت في الموعد ÷ إجمالي التذاكر)"),
	("CW-MNT-04", "Customer Satisfaction", "رضا العميل", "Maintenance", 20,
	 "Visits: Customer Satisfaction", "Average customer rating ÷ 5 (متوسط تقييم العميل ÷ 5)"),
	("CW-SAL-01", "Sales Target Achievement", "تحقيق تارجت المبيعات", "Sales", 50,
	 "Sales: Revenue vs Target", "Actual sales ÷ monthly target (المبيعات الفعلية ÷ التارجت الشهري)"),
	("CW-SAL-02", "New Customers", "العملاء الجدد", "Sales", 25,
	 "Sales: New Customers vs Target", "New customers ÷ target (عملاء جدد فعلياً ÷ المستهدف)"),
	("CW-SAL-03", "Visits & Technical Offers", "عدد الزيارات والعروض الفنية", "Sales", 25,
	 "Sales: Quotations vs Target", "Visits and offers made ÷ target (زيارات وعروض منفذة ÷ المستهدف)"),
	("CW-KIT-01", "Complete Instruments & Tools", "اكتمال الأجهزة والأدوات", "Kit & Tools Readiness", 40,
	 "Manual Entry", "Items present ÷ items on the required list (عناصر موجودة ÷ عناصر القائمة المطلوبة)"),
	("CW-KIT-02", "Valid & Calibrated Instruments", "صلاحية ومعايرة الأجهزة", "Kit & Tools Readiness", 40,
	 "Manual Entry", "Sound and calibrated instruments ÷ all instruments (أجهزة سليمة ومعايرة ÷ إجمالي الأجهزة)"),
	("CW-KIT-03", "Supplies Available", "توفر المستلزمات", "Kit & Tools Readiness", 20,
	 "Manual Entry", "Supplies available ÷ required (مستلزمات متوفرة ÷ المطلوبة)"),
	("CW-REP-01", "Visit Reports", "تقارير الزيارات", "Reports to Management", 40,
	 "Visits: Reports On Time", "Reports submitted on time and complete ÷ required (تقارير مقدمة في الموعد ومكتملة ÷ المطلوبة)"),
	("CW-REP-02", "Technical Reports", "التقارير الفنية", "Reports to Management", 30,
	 "Manual Entry", "Reports submitted on time and complete ÷ required (تقارير مقدمة في الموعد ومكتملة ÷ المطلوبة)"),
	("CW-REP-03", "Sales & Other Reports", "تقارير المبيعات وباقي التقارير", "Reports to Management", 30,
	 "Manual Entry", "Reports submitted on time and complete ÷ required (تقارير مقدمة في الموعد ومكتملة ÷ المطلوبة)"),
	("CW-APP-01", "Uniform", "الزي الرسمي", "Appearance & Safety", 40,
	 "Manual Entry", "Times compliant ÷ times checked (مرات الالتزام ÷ مرات المراجعة)"),
	("CW-APP-02", "Safety Vest", "الـ Vest", "Appearance & Safety", 30,
	 "Manual Entry", "Times compliant ÷ times checked (مرات الالتزام ÷ مرات المراجعة)"),
	("CW-APP-03", "Safety Equipment", "معدات السلامة (Safety)", "Appearance & Safety", 30,
	 "Manual Entry", "Times compliant ÷ times checked (مرات الالتزام ÷ مرات المراجعة)"),
]

SALES_SOURCES = ("Sales: Revenue vs Target", "Sales: New Customers vs Target", "Sales: Quotations vs Target")


def seed_scorecard():
	if not frappe.db.exists("DocType", "CW KPI Category"):
		return

	for name, arabic, _weight, description in CATEGORIES:
		if not frappe.db.exists("CW KPI Category", name):
			frappe.get_doc(
				{"doctype": "CW KPI Category", "category_name": name, "arabic_name": arabic, "description": description}
			).insert(ignore_permissions=True)

	for code, name, arabic, category, weight, source, method in CRITERIA:
		if frappe.db.exists("CW KPI Definition", code):
			continue
		frappe.get_doc(
			{
				"doctype": "CW KPI Definition",
				"kpi_code": code,
				"kpi_name": name,
				"arabic_name": arabic,
				"kpi_category": category,
				"kpi_type": "Percentage Target",
				"directionality": "Higher is Better",
				"data_source": source,
				"unit": "%",
				"is_active": 1,
				"default_weight": weight,
				"min_score": 0,
				"max_score": 100,
				"cap_achievement_percent": 100,
				"measurement_method": method,
			}
		).insert(ignore_permissions=True)

	if frappe.db.exists("CW KPI Target Template", TEMPLATE):
		return
	template = frappe.get_doc(
		{
			"doctype": "CW KPI Target Template",
			"template_name": TEMPLATE,
			"is_active": 1,
			"description": "Quarterly evaluation with a monthly review, rated by the direct manager (technical and "
			"commercial manager). Eligible for the incentive only when the total is at least 85% and every "
			"category at least 70%. Set each engineer's monthly sales targets on their KPI plan.",
			"evaluation_cycle": "Quarterly",
			"months_required": 3,
			"missing_data_policy": "Exclude and Reweight",
			"pass_total_score": 85,
			"min_category_score": 70,
			"categories": [{"kpi_category": name, "weight": weight} for name, _ar, weight, _d in CATEGORIES],
			"template_items": [
				{
					"kpi_definition": code,
					"kpi_name": name,
					"kpi_category": category,
					"weight": weight,
					# Ratio criteria are measured against 100%; sales targets are per engineer.
					"target_value": 0 if source in SALES_SOURCES else 100,
				}
				for code, name, _ar, category, weight, source, _m in CRITERIA
			],
		}
	)
	template.insert(ignore_permissions=True)
