app_name = "cw_kpi_management"
app_title = "KPI"
app_publisher = "Nest Software Development"
app_description = "Employee KPI Management & Calculation Engine for ERPNext v16"
app_email = "info@nsd-eg.com"
app_license = "mit"

# Dependencies
required_apps = ["erpnext"]

# Desk app (Frappe v16.51+: Apps screen tile, rail in dock/, sidebars in kpi_management/sidebar/).
app_logo_url = "/assets/cw_kpi_management/images/kpi.png"
app_home = "/desk/kpi-management"

add_to_apps_screen = [
	{
		"name": "cw_kpi_management",
		"logo": "/assets/cw_kpi_management/images/kpi.png",
		"title": "KPI",
		"route": "/desk/kpi-management",
		"has_permission": "cw_kpi_management.desk.has_app_permission",
	}
]

# Module icons for the rail and the sidebar headers.
app_include_icons = ["/assets/cw_kpi_management/icons/kpi-icons.svg"]

after_install = "cw_kpi_management.desk.after_install"
after_migrate = ["cw_kpi_management.desk.after_migrate"]

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
	"CW KPI Monthly Review": "cw_kpi_management.kpi_management.doctype.cw_kpi_monthly_review.cw_kpi_monthly_review.get_permission_query_conditions",
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
