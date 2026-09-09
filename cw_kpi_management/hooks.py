app_name = "cw_kpi_management"
app_title = "C-Water KPI Management"
app_publisher = "Nest Software Development"
app_description = "Employee KPI Management & Calculation Engine for ERPNext v16"
app_email = "info@nsd-eg.com"
app_license = "mit"

# Dependencies
required_apps = ["erpnext"]

# Document Events
doc_events = {
	"CW KPI Evaluation": {
		"on_submit": "cw_kpi_management.payroll_integration.on_evaluation_submit",
	}
}

# Permission query conditions
permission_query_conditions = {
	"CW KPI Evaluation": "cw_kpi_management.kpi_management.doctype.cw_kpi_evaluation.cw_kpi_evaluation.get_permission_query_conditions",
	"CW Employee KPI Plan": "cw_kpi_management.kpi_management.doctype.cw_employee_kpi_plan.cw_employee_kpi_plan.get_permission_query_conditions",
}

# Fixtures to export/install
fixtures = [
	{
		"dt": "Role",
		"filters": [
			["name", "in", ["CW KPI Administrator", "CW Department Manager"]]
		]
	},
	{
		"dt": "CW KPI Definition",
		"filters": [["name", "!=", ""]]
	},
	{
		"dt": "CW KPI Compensation Rule",
		"filters": [["name", "!=", ""]]
	}
]
