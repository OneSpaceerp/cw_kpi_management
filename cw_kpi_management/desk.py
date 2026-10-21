# Copyright (c) 2026, Nest Software Development & C-Water
# For license information, please see license.txt

"""Desk integration: who sees the KPI app, and keeping its navigation current.

Frappe v16.51 draws the desk from three things an app ships: a tile on the Apps screen
(`add_to_apps_screen`), a rail of shells (`dock/`) and one sidebar per shell
(`kpi_management/sidebar/`). Older v16 releases ignore the last two and keep using the
workspace.
"""

import frappe

APP = "cw_kpi_management"
MODULE = "KPI Management"

# Roles that work in the KPI desk app. Employees see their own plans and evaluations through
# the list views; they do not get an app tile.
APP_ROLES = {
	"System Manager",
	"CW KPI Administrator",
	"CW Department Manager",
	"HR Manager",
	"HR User",
	"Accounts Manager",
}

# Shipped navigation, as (doctype, name, path inside the module folder).
SHIPPED = (
	("Workspace", "KPI Management", ("workspace", "kpi_management")),
	("Workspace", "KPI Payroll", ("workspace", "kpi_payroll")),
	("Sidebar", "KPI Management", ("sidebar", "kpi_management")),
	("Sidebar", "KPI Payroll", ("sidebar", "kpi_payroll")),
	("Sidebar", "KPI Setup", ("sidebar", "kpi_setup")),
)

DESKTOP_ICON = {
	"icon_type": "App",
	"link_type": "External",
	"link": "/desk/kpi-management",
	"logo_url": "/assets/cw_kpi_management/images/kpi.png",
	"app": APP,
	"standard": 1,
	"hidden": 0,
}


def has_app_permission(user: str | None = None) -> bool:
	"""`add_to_apps_screen` gate: show the KPI tile to the roles that use it."""
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	return bool(APP_ROLES.intersection(frappe.get_roles(user)))


def after_install():
	after_migrate()


def after_migrate():
	ensure_shipped_navigation()
	ensure_desktop_icon()
	frappe.clear_cache()


def ensure_shipped_navigation():
	"""Make the KPI workspaces and sidebars the ones this app ships.

	A migrate skips an app's file whenever the site holds a record of the same name that looks
	newer. Upgrading to Frappe v16.51 converts a site's old sidebars into `Sidebar` records, and
	Frappe also creates a "KPI Management" sidebar for the module on its own, so the names this
	app ships can already be taken. Re-import the app's file over any record that is not the
	app's. Does nothing once they are.
	"""
	from frappe.modules.import_file import import_file_by_path

	for doctype, name, folder in SHIPPED:
		if not frappe.db.exists("DocType", doctype):
			continue  # Sidebar only exists from v16.51
		current = frappe.db.get_value(doctype, name, ["standard", "module"], as_dict=True)
		if current and current.standard and current.module == MODULE:
			continue

		path = frappe.get_module_path(MODULE, *folder, f"{folder[-1]}.json")
		frappe.flags.in_import = True
		try:
			import_file_by_path(path, force=True, ignore_version=True)
		finally:
			frappe.flags.in_import = False


def uses_desktop_icon_grid() -> bool:
	"""Whether the desk home is the Desktop Icon grid: always before v16.51, a choice after."""
	try:
		from frappe.desk.doctype.desktop_settings.desktop_settings import is_desktop_icons_page
	except ImportError:
		return True
	return is_desktop_icons_page()


def ensure_desktop_icon():
	"""Give the icon grid a KPI tile with the app's logo. On the v16.51 Apps screen the tile
	comes from `add_to_apps_screen`, and such a site holds no icon rows at all."""
	if not frappe.db.exists("DocType", "Desktop Icon") or not uses_desktop_icon_grid():
		return

	if frappe.db.exists("Desktop Icon", "KPI"):
		current = frappe.db.get_value("Desktop Icon", "KPI", list(DESKTOP_ICON), as_dict=True)
		if any(current.get(key) != value for key, value in DESKTOP_ICON.items()):
			frappe.db.set_value("Desktop Icon", "KPI", DESKTOP_ICON)
	else:
		icon = frappe.get_doc({"doctype": "Desktop Icon", "label": "KPI", **DESKTOP_ICON})
		icon.flags.ignore_permissions = True
		icon.insert()

	# Frappe made a plain "KPI Management" tile for the workspace before the app had its own;
	# two tiles for one app is confusing, so hide that one (it is kept, not deleted).
	auto = frappe.db.get_value("Desktop Icon", MODULE, ["icon_type", "hidden"], as_dict=True)
	if auto and auto.icon_type != "App" and not auto.hidden:
		frappe.db.set_value("Desktop Icon", MODULE, "hidden", 1)

	frappe.cache.delete_key("desktop_icons")
