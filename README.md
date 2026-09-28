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

## License
MIT License. Copyright (c) 2026 Nest Software Development & C-Water.
