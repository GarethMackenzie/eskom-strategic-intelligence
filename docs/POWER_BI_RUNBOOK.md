# Power BI Desktop and Service Runbook

## What GitHub contains

GitHub stores the complete editable Power BI Project:

- `EskomStrategicIntelligence.pbip` — project entry point
- `EskomStrategicIntelligence.Report/` — enhanced PBIR report definition
- `EskomStrategicIntelligence.SemanticModel/` — TMDL semantic model

This is real Power BI source control, not a screenshot or a placeholder. GitHub does not execute the
Power BI rendering engine, so an interactive browser report must be published to Power BI Service.

## Desktop validation

1. Install a current Power BI Desktop release.
2. Clone or download the repository.
3. Open `EskomStrategicIntelligence.pbip`.
4. Confirm that all six model tables and three relationships load.
5. Refresh the semantic model.
6. Check all five pages and verify that cards, charts and evidence tables render.
7. Confirm these displayed values:
   - FY2027/28 average path: 8.83%
   - FY2026/27 direct increase: 8.76%
   - FY2026/27 municipal increase: 9.01%
   - FY2026 year-end municipal arrears: R111.6bn
   - June 2026 in-year municipal arrears: R119.9bn
   - electricity sales: 178 TWh
   - EAF: 65.16%
   - net profit after tax: R30.3bn
8. Confirm the tariff page says the detailed retail structure was under consultation at
   4 September 2026 and does not describe 8.83% as a final customer-category tariff.

On first open from a clean checkout, press **Esc** to leave Power BI's Home view, then use both
**Refresh now** prompts to apply the relationships and populate the inline tables.

### Recorded Desktop validation

Validated on 7 September 2026 in Power BI Desktop 2.157.1354.0 (August 2026):

- the `.pbip` opened and the six-table semantic model loaded;
- all inline tables refreshed (9 period rows, 14 metric rows, 4 tariff rows, 1 scenario row,
  38 source-register rows and the measure-catalog seed row);
- all three relationships applied;
- all five report pages rendered without model or visual errors;
- the expected debt, tariff, sales, EAF, profit and governance values displayed correctly.

The live test exposed and resolved two generator compatibility defects before release: invalid
inline Power Query type tokens and Power BI's reserved `Measures` table name. Automated regression
coverage now protects both fixes.

## Power BI Service publication

1. In Power BI Desktop, choose **Publish**.
2. Sign in with the account authorised for the target workspace.
3. Select the intended workspace and publish the semantic model and report.
4. In Power BI Service, open the report and repeat the five-page interaction check.
5. Configure permissions. Do not enable public “Publish to web” unless the data owner intentionally
   accepts fully public, unauthenticated access.
6. Add the verified Service URL to the README only after the report opens successfully in a clean
   browser session with the intended permission model.

## Current status

The editable project is source-validated and Power BI Desktop-runtime-validated. Power BI Service
publication remains intentionally separate because it requires selection of an authorised target
workspace and its permission model.

| Gate | Status |
|---|---|
| PBIP/PBIR/TMDL source generated | PASS |
| Automated structural QA | PASS |
| SQLite/data QA | PASS |
| GitHub Actions | Pending this release push |
| Power BI Desktop runtime | PASS — 2.157.1354.0 (August 2026), 7 Sep 2026 |
| Power BI Service publication | Not yet published |
