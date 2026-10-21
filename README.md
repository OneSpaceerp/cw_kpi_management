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
*Current test suite: 28 / 28 tests passing (16 of them for the engineer scorecard).*

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

## Engineer scorecard (C-Water evaluation sheet)

`CWater_Engineers_KPI_Calculator.xlsx` is built in: installing or migrating seeds
the **C-Water Engineer Scorecard** template with its 5 categories (Maintenance 40%,
Sales 20%, Kit & Tools 15%, Reports 15%, Appearance & Safety 10%) and 16 criteria
(codes `CW-MNT-01` ... `CW-APP-03`), inserted once and never overwritten.

**Flow**

1. **KPI Plan** per engineer and quarter (KPI Period, e.g. "Q4 2026"): choose the
   template; categories, criteria and thresholds are copied. Enter the engineer's
   monthly sales targets on the Sales lines.
2. **Monthly Review** (Plan > Actions > Monthly Review): one per engineer and month.
   *Fetch Data* fills the automatic criteria; the manager enters the others (as
   achieved ÷ required, or a percentage, or "Not Measured"). Submitting it gives the
   monthly indicator (On Track / Needs Improvement, with what needs attention). It
   never pays anything.
3. **KPI Evaluation** for the quarter: *Calculate* averages the submitted monthly
   reviews and decides **Eligible / Not Eligible / Incomplete** with the reasons.
   Approving an Eligible evaluation creates the payroll result from the
   Compensation Rules (if *Auto Generate Payroll on Approval* is on); any other
   decision creates none.

**Automatic criteria**: visits plan adherence, fault response within SLA, tickets
closed on time, visit reports on time and complete, customer satisfaction (from
the Visits app); sales vs target, new customers, quotations (from the Sales Person
linked to the employee). Kit, appearance & safety, technical and sales reports are
entered by the manager.

**What the sheet did and what the app does**

| The sheet | The app |
| --- | --- |
| Only category weights were checked | Both levels must total 100%; a plan or template that does not is refused |
| 100% cap only by cell validation | Every achievement is clamped to 0-100% on the server |
| A criterion with no data scored 0% | *Criterion With No Data*: **Exclude and Reweight** (default; its weight is shared by the measured criteria of its category, and the evaluation says so) or **Count as Zero** (the sheet's rule) |
| A month and the quarter treated blanks differently | One rule for both |
| A decision with 1-2 of 3 months entered | Fewer submitted monthly reviews than required gives **Incomplete**, no payment |
| 84.96% displayed as 85.0% and failed | Scores are rounded once (half up, *Score Decimals*), then compared |
| Monthly "on track" ignored the 70% minimum | On track only if the total and every category meet their thresholds |
| No year on the quarter | Periods are named with their year automatically (Q4 2026) |
| One file per engineer, no history | One plan per engineer, submitted reviews, audited overrides, Engineer Scorecard report |

Thresholds (85% total, 70% per category, reviews per quarter, missing-data rule)
are on the template/plan, with defaults in CW KPI Settings. A category can have its
own minimum. The incentive **amount** is not in the sheet; it comes only from the
Compensation Rules C-Water defines.

## Desk app (ERPNext v16.51+)

KPI is a desk app of its own: a **KPI** tile on the Apps screen (logo
`public/images/kpi.png`) and a rail with three sections, each with its own sidebar.

| Rail | Sidebar | Holds |
| --- | --- | --- |
| Performance | KPI Management | Home dashboard, Employee KPI Plan, Monthly Review, KPI Evaluation, KPI Period, Metric Snapshot, Reports (Engineer Scorecard) |
| Payroll | KPI Payroll | Payroll dashboard, KPI Payroll Result, Compensation Rule, Additional Salary, Salary Component, Salary Slip, Payroll Entry, Reconciliation report |
| Setup | KPI Setup | KPI Definition, Target Template, KPI Category, Compensation Rule, Organization, Access, Settings (KPI, HR, Payroll) |

The two home pages (`/desk/kpi-management`, `/desk/kpi-payroll`) show live number
cards and charts: active plans, evaluations awaiting review, average approved
score, open periods, payouts queued and processed.

Files: `dock/` (rail); the sidebars and home pages in `kpi_management/`,
`kpi_payroll/` and `kpi_setup/`; number cards and charts in
`kpi_management/number_card/` and `kpi_management/dashboard_chart/`; icons in
`public/icons/kpi-icons.svg`. KPI Payroll and KPI Setup are navigation-only
modules (all DocTypes stay in KPI Management): the desk gives a workspace to the
first sidebar of the workspace's module, so each rail section needs a module of
its own to keep its home page. The tile
shows for System Manager, CW KPI Administrator, CW Department Manager, HR Manager,
HR User and Accounts Manager (`desk.py`). After every migrate, `desk.py` re-imports
the shipped workspaces and sidebars over any record a site made or converted
under the same name, and adds the KPI tile on sites that use the Desktop Icon grid.

## License
MIT License. Copyright (c) 2026 Nest Software Development & C-Water.
