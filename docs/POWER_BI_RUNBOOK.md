# Power BI Desktop and Service Runbook

## Source-controlled deliverable

The repository contains an editable Power BI Project rather than a binary preview:

- `EskomStrategicIntelligence.pbip` — project entry point
- `EskomStrategicIntelligence.Report/` — enhanced PBIR report definition
- `EskomStrategicIntelligence.SemanticModel/` — TMDL semantic model
- `powerbi/dax/measures.dax` — generated, reviewable copy of the measures

Do not hand-edit generated model, report, or DAX files. Change the governed SQL or
`scripts/build_powerbi_project.py`, then run:

```powershell
python scripts/build_project.py
python -m pytest -q
```

The build order is SQLite schema and governed facts, release-blocking QA, then Power BI generation.
The semantic model is produced only from the allow-listed `vw_powerbi_*` views.

## Desktop validation procedure

1. Install a current Power BI Desktop release.
2. Clone the repository and run the build and tests above.
3. Open `EskomStrategicIntelligence.pbip`.
4. Confirm that all six model tables, three relationships, and 34 explicit measures load.
5. Review all five pages at the intended display size and test cross-filtering and tooltips.
6. Confirm the headline values listed below.
7. Save only if you intend to review Desktop's metadata changes before committing them; the generator
   remains the source of truth.

Expected headline values:

| Metric | Expected result |
|---|---:|
| FY2026 year-end municipal arrears | R111.6bn |
| Prior year-end municipal arrears | R94.6bn |
| Year-on-year arrears growth | 17.97% |
| FY2015–FY2026 arrears CAGR | 32.62% |
| June 2026 in-year municipal arrears | R119.9bn |
| Latest electricity sales | 178 TWh |
| Sales year-on-year change | -6.17% |
| Latest energy availability factor | 65.16% |
| EAF change | +4.56 percentage points |
| Net profit after tax | R30.3bn |
| Illustrative tariff index | 133.44 |
| Governed sources | 40 |
| Latest actual evidence date | 2 September 2026 |

The 8.83% FY2027/28 average path is not a final customer-category tariff. The tariff page must retain
the separate NERSA retail-structure consultation status and its 2 September 2026 evidence date.

## Final human visual and accessibility checklist

Status: **PASS — user-confirmed final review completed**

The final reviewed report was inspected at its intended 1280 × 720 page size. The checklist below
records PASS/FAIL for each actual PBIR page without inventing reviewer identity, review time or a
separate Desktop version for the human review.

| Page | Page opens | Layout and text | Interactions | Evidence and values | Accessibility |
|---|---|---|---|---|---|
| Executive Overview | PASS | PASS | PASS | PASS | PASS |
| Tariff & Affordability | PASS | PASS | PASS | PASS | PASS |
| Municipal Debt | PASS | PASS | PASS | PASS | PASS |
| Operations & Security | PASS | PASS | PASS | PASS | PASS |
| Data Governance | PASS | PASS | PASS | PASS | PASS |

For every page, confirm:

- no clipping, unwanted scrollbars, overlapping objects, unreadable text or hidden visual errors;
- KPI formatting, units, titles and all headline values reconcile to the expected results above;
- slicers, cross-filtering and tooltips behave correctly;
- scenarios are visibly distinct from actuals and required source/evidence qualifiers remain visible;
- colour does not mislead, contrast and reading order are reasonable, and the page remains usable at
  the intended display resolution.

Automated tests cover page/visual counts, JSON parsing, field and measure resolution, theme and
PBIR/TMDL references, canvas bounds, prohibited overlaps, absolute paths and credential-like text.
They do not complete this human checklist.

## Recorded Desktop validation

Validated on 8 September 2026 in Power BI Desktop 2.157.1354.0 (August 2026):

- the PBIP opened and a live local Analysis Services catalog loaded;
- all 34 measures reported a valid engine state with no error message;
- a live DAX query returned the expected headline values above;
- the loaded tables contained 21 period rows, 29 metric rows, 4 tariff rows, 1 scenario row, and 40
  source-register rows;
- the five-page, 68-visual PBIR definition passed automated structural and field-reference checks;
- compatibility level 1606 loaded successfully.

Desktop testing exposed three release defects that were fixed before this validation:

1. compatibility level 1600 attempted to downgrade Desktop's 1606 model;
2. `Path` was parsed as an invalid DAX variable name;
3. `FirstDate` collided with the DAX `FIRSTDATE` function name.

Regression tests now cover compatibility level 1606 and the reserved identifiers. The live-engine
test proves model compilation and measure execution. The user subsequently confirmed completion of
the final five-page visual and accessibility review at the target screen size.

## Power BI Service publication

1. Open the validated PBIP in Power BI Desktop and choose **Publish**.
2. Sign in with the account authorised for the target workspace.
3. Select the intended workspace and publish the semantic model and report.
4. Open the report in Power BI Service and repeat the five-page interaction and accessibility check.
5. Configure least-privilege permissions. Do not use public **Publish to web** unless the data owner
   deliberately accepts unauthenticated public access.
6. Add a Service URL to the README only after it succeeds in a clean browser session with the intended
   permission model.

## Release gates

| Gate | Status |
|---|---|
| PBIP/PBIR/TMDL generated from governed SQLite views | PASS |
| SQL and source-register QA | PASS — 17 checks |
| Python test suite | PASS — 32 tests |
| Static PBIR structure | PASS — 5 pages, 68 visuals |
| Power BI Desktop model runtime | PASS — 2.157.1354.0, 8 Sep 2026 |
| Human visual/accessibility sign-off | PASS — user-confirmed final review completed |
| Power BI Service publication | Requires authorised workspace selection |
