# C-Water KPI Management (`cw_kpi_management`)

Custom ERPNext v16 application for C-Water to manage employee KPI plans, mathematical scoring calculations, multi-level approvals, manual overrides with full audit logging, and upgrade-safe ERPNext payroll integration.

## Key Features
- **Configurable KPI Definitions**: Reusable metrics supporting Target Achievement, Count Targets, Percentage Targets, Thresholds, Range-based scoring, Attendance-derived actuals, Manager Ratings, and Composite metrics.
- **Directionality & Scoring Rules**: Support for Higher-is-Better, Lower-is-Better, Range-is-Best, Pass/Fail, achievement caps, floors, score scaling, and custom weights.
- **Employee Plans & Periods**: Assign tailored KPI targets and weights by employee, designation, and period (monthly, quarterly, semi-annual, annual). Strict validation ensures weights sum to 100%.
- **Deterministic Server-Side Calculation Engine**: Raw metric capture from ERPNext transactions (Sales Invoices, Quotations, Site Visits, Attendance) and deterministic formula execution with immutable calculation audit trails.
- **Audited Manual Overrides**: Field-level score adjustments require previous value, new value, justification reason, authorizer, and approval.
- **Controlled Payroll Integration**: Evaluates approved KPI scores against configurable Compensation Rules to generate `CW KPI Payroll Result` records, handing off to ERPNext standard `Additional Salary` (Bonus, Commission, Deduction, Allowance) without touching core payroll code.

## Documentation & Testing Guides
- [**Step-by-Step Testing & UAT Guide**](docs/KPI_TESTING_STEP_BY_STEP_GUIDE.md): Complete testing procedure from KPI Definition to ERPNext Salary Slip creation.
- [**KPI Calculation Formulas Guide**](docs/KPI_CALCULATION_GUIDE.md): Mathematical formulas for all 8 KPI metric types, floors, caps, and directionality.
- [**Payroll Integration Guide**](docs/PAYROLL_INTEGRATION_GUIDE.md): Specification for Compensation Rules and automatic handoff to standard ERPNext `Additional Salary`.

## Automated Unit Testing
Run the automated test suite locally:
```bash
python -m pytest cw_kpi_management/tests -v
```
*Current test suite: 12 / 12 tests passing.*

## Installation
```bash
bench get-app https://github.com/OneSpaceerp/cw_kpi_management.git
bench --site onespace.cw-eg.com install-app cw_kpi_management
bench --site onespace.cw-eg.com migrate
```

Updating an installed site:
```bash
cd apps/cw_kpi_management && git pull && cd ../..
bench --site onespace.cw-eg.com migrate
bench build --app cw_kpi_management
bench --site onespace.cw-eg.com clear-cache
bench restart
```

## Desk app (ERPNext v16.51+)

KPI is a desk app of its own: a **KPI** tile on the Apps screen (logo
`public/images/kpi.png`) and a rail with three sections, each with its own sidebar.

| Rail | Sidebar | Holds |
| --- | --- | --- |
| Performance | KPI Management | Home dashboard, Employee KPI Plan, KPI Evaluation, KPI Period, Metric Snapshot, Reports |
| Payroll | KPI Payroll | Payroll dashboard, KPI Payroll Result, Compensation Rule, Additional Salary, Salary Component, Salary Slip, Payroll Entry, Reconciliation report |
| Setup | KPI Setup | KPI Definition, Target Template, Compensation Rule, Organization, Access, Settings (KPI, HR, Payroll) |

The two home pages (`/desk/kpi-management`, `/desk/kpi-payroll`) show live number
cards and charts: active plans, evaluations awaiting review, average approved
score, open periods, payouts queued and processed.

Files: `dock/` (rail), `kpi_management/sidebar/` (sidebars),
`kpi_management/workspace/`, `kpi_management/number_card/`,
`kpi_management/dashboard_chart/`, icons in `public/icons/kpi-icons.svg`. The tile
shows for System Manager, CW KPI Administrator, CW Department Manager, HR Manager,
HR User and Accounts Manager (`desk.py`). After every migrate, `desk.py` re-imports
the shipped workspaces and sidebars over any record a site made or converted
under the same name, and adds the KPI tile on sites that use the Desktop Icon grid.

## License
MIT License. Copyright (c) 2026 Nest Software Development & C-Water.
