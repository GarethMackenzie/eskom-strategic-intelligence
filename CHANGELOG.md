# Changelog

## [GitHub preview fallback] - 2026-09-09

- Added a 1280×720 PNG rendering of the governed SVG dashboard preview.
- Switched the README inline preview to PNG so it does not depend on GitHub's SVG rendering proxy.
- Added regression checks for the PNG signature, dimensions, README reference and source-SVG hash.

## [Final integrity release] - 2026-09-08

### Corrected

- Replaced the incorrect FY2024 R55.3bn total-arrears value with Eskom's official R74.4bn.
- Reclassified R55.3bn as the National Treasury-approved legacy-debt scope of the Municipal Debt
  Relief Programme and isolated it from the annual arrears fact.
- Removed the false FY2024 source-conflict table and reconciled the rounded CFO testimony to the
  exact Eskom FY2024/FY2025 values.
- Replaced the three-point arrears history with the official FY2015–FY2026 series.
- Upgraded the FY2027/28 ERTSA consultation status to NERSA's official 2 September 2026 source.

### Engineering

- Made SQLite the canonical Power BI data source through five validated semantic export views.
- Reordered the build to database → QA → Power BI, blocking artifact generation on failed checks.
- Replaced fixed DAX comparators, dates and tariff-rate literals with dynamic period/table logic.
- Established one measure catalog that generates TMDL and the DAX review export.
- Expanded build-time checks from 11 to 17 and added regression tests for the full debt series,
  programme scope, semantic lineage, generator literals and measure-catalog parity.
- Added Ruff lint/format gates and clean deterministic double-build checks to CI.
- Completed the MIT license text and named the copyright holder.
- Raised the generated Tabular compatibility level from 1600 to 1606 after Power BI Desktop
  2.157.1354.0 reported an illegal compatibility downgrade; added regression coverage.
- Renamed reserved DAX variables (`Path` and `FirstDate`) after live-engine metadata exposed both
  parser failures; all 34 measures now compile and execute in Desktop.
- Made semantic-model generation remove stale Desktop local-date and legacy-role artifacts before
  rebuilding, with auto time intelligence disabled for deterministic source control.

### Documentation and Power BI

- Regenerated the five-page PBIR/TMDL project and source-driven SVG preview.
- Reconciled the report, README, data model, KPI dictionary, limitations, audit, scorecard and
  runbook with the corrected source scopes and architecture.
- Added `docs/release_manifest.md` as the final auditable release record.
- Recorded live Desktop engine results for all headline measures and semantic-table row counts.

## [SVG preview repair] - 2026-09-07

- Escaped the ampersand in the generated dashboard preview so GitHub can render the SVG.
- Added XML parsing to the preview regression test.

## [Phase 4 Power BI release] - 2026-09-07

### Corrected

- Replaced invalid inline Power Query `type` field tokens with Desktop-compatible M tokens.
- Renamed the reserved `Measures` semantic-model table to `MeasureCatalog` and updated every PBIR
  visual binding.

### Verified

- Power BI Desktop 2.157.1354.0 (August 2026) opened and refreshed the project successfully.
- All six tables, three relationships, five pages, 68 visuals and 30 DAX measures loaded without
  engine or visual errors.
- 11 build-time data checks and 27 pytest release tests pass.
- Power BI Service publication remains intentionally pending an authorised target workspace.

## [Phase 4 Power BI release candidate] - 2026-09-04

### Added

- Complete source-controlled `EskomStrategicIntelligence.pbip` project.
- Enhanced PBIR report with 5 executive pages, 68 visuals and page-level slicers.
- TMDL semantic model with 6 tables, 3 relationships and 30 explicit DAX measures.
- Tariff and affordability page covering implemented FY2026/27 rates and the qualified 8.83%
  FY2027/28 average path.
- Deterministic Power BI build generator and labelled SVG project preview.
- `docs/POWER_BI_RUNBOOK.md` covering Desktop validation and safe Service publication.
- Three governed tariff sources (DS035-DS037), a tariff fact table and reporting view.
- Power BI structural, lineage and no-local-path release tests.

### Verified

- 11 build-time data checks pass.
- 26 pytest release tests pass, including a no-overlap canvas regression check.
- All Power BI JSON parses, all visual measure references resolve and all project paths are
  portable.

### Remaining runtime gate

- Power BI Desktop open/refresh/interaction and Power BI Service publication must be verified in
  those products before the project is described as a live interactive dashboard.

## [Release review] - 2026-09-04

### Corrected

- Repaired obsolete schema references and SQLite-incompatible expressions in the profiling and
  data-quality SQL.
- Added a dedicated fiscal-year-end municipal-debt DAX measure so YoY calculations cannot use the
  June 2026 in-year snapshot.
- Reclassified primary-source evidence for EAF, municipal-debt projection, capex and estimated
  surplus capacity using Eskom's 31 August 2026 results release.
- Split the mixed capex record into reported actual and forward guidance records.

### Added

- One-command SQLite build (`scripts/build_project.py`).
- Standard-library source-register ingestion and automated validation modules.
- Nine build-time integrity checks and 17 pytest release tests.
- CI compilation, full database build, pytest and generated-output validation.

### Remaining limitation

- Power BI Desktop runtime validation and a completed `.pbix`/`.pbip` remain outstanding and are
  not claimed.

## [Phase 2] — 2026-09-04
### Remediation context
Full technical audit performed against Phase 1 (`docs/technical_audit.md`), classifying defects
P0 (factual/data-integrity) through P3 (cosmetic). All identified P0 and P1 defects were fixed in
this pass; see the audit document for the complete list. Summary of the most significant fixes:

### Fixed — P0 (data-integrity)
- Secondary press URLs no longer classified `A-Primary`. Source register rebuilt with separate
  `originating_entity` / `source_publisher` / `source_tier` (A1/A2/B/C) columns; every one of the
  28 Phase-1 sources individually re-rated (most downgraded B where only secondary reporting
  existed). 5 new sources added, bringing the total to 33.
- `fact_security_case_log`'s reused source ID (DS019 wrongly cited for 3 unrelated cases) fixed:
  each case now has its own dataset ID (DS026, DS027, DS028) resolving to the article that
  actually describes it.
- `Total Municipal Debt` DAX bug fixed: an unfiltered card previously summed multiple point-in-time
  balances into a fabricated total (reproduced and confirmed: R326.1bn in the 3-row Phase-1 state).
  Replaced with `Latest Reported Municipal Debt`, using explicit LATEST-observation resolution.
- `Data As Of` DAX bug fixed: previously `MAX(dim_date[calendar_date])`, which could resolve to the
  2031 scenario horizon date. Replaced with `fact_source_refresh`/`Data Reported As Of`, which
  structurally excludes scenario dataset IDs at load time.
- Scenario rows physically separated into `fact_municipal_debt_scenario`, a table with no shared
  grain with `fact_municipal_debt`, so no SUM/JOIN can accidentally blend actual and scenario data.

### Fixed — P1 (could materially mislead)
- `fact_security_incidents` (five metrics bundled under one shared source ID) replaced with
  `fact_security_metric` at (reporting_date × incident_scope × metric × location) grain — each
  observation has its own source_dataset_id.
- `legal_status = 'Mixed (Arrest+Conviction, aggregated across cases)'` — a non-atomic, ambiguous
  value — eliminated. New `dim_legal_status` controlled vocabulary; new `fact_security_case` /
  `fact_security_case_event` model supports multiple chronological legal events per case without
  overwriting history. The former "mixed" row was reclassified as a metric-level observation
  (it was genuinely a financial-impact aggregate across multiple cases, not one traceable case).
- `docs/data_model.md` group-total status semantics corrected: `dim_debt_status` now distinguishes
  "Aggregate Exposure" (group-total grain) from genuine individual-municipality operational status.
- Report language rewritten to neutral, evidence-led tone (removed unattributed editorial framing);
  the City of Johannesburg case is now explicitly scoped as "a documented example," not proof that
  mediation generally works.
- Full structured recommendation framework (problem/evidence/mechanism/impact direction/
  difficulty/dependencies/risk/owner/horizon/KPI/data required/confidence) applied to all three
  strategic problems, not just one.

### New research this pass
- **NERSA's own tariff decision document** located (nersa.org.za), upgrading DS008 to source-tier
  A1 and correcting a Phase-1 error: municipal tariff increase is 11.32%, not the same 12.74%
  applied to direct customers.
- **National Treasury's MFMA Circular 124** and May-2025 Budget Review Annexure A located,
  upgrading DS023 to A1 and providing the actual debt-relief programme conditions (≥85% revenue
  collection, cost-reflective tariffs, 30-day payment terms, etc.) instead of a vague qualitative
  claim.
- **Parliamentary Monitoring Group (PMG)** committee minutes and Questions-to-Ministers records
  located — genuine A1 primary parliamentary sources — providing: a third historical year-end debt
  figure (R55.3bn FY2024, corroborated two ways), debt-relief compliance detail (15 of 71
  consistently compliant per one source, 61 of 71 found non-compliant per another), R47.173bn in
  new arrears accumulated by debt-relief participants since April 2023, and a provincial debt
  concentration figure (Mpumalanga R30.5bn, Free State R29.1bn).
- **New reconciliation item surfaced, not resolved:** PMG committee testimony (Eskom CFO) gives a
  different FY2024 municipal-arrears figure (~R74bn) than the Treasury/MTBPS-sourced figure
  (R55.3bn) for the same date. Both retained; discrepancy documented in `docs/limitations.md`.

### Data gaps: status change
- **Data Gap #1** (municipality-level arrears): PARTIALLY CLOSED — provincial-level concentration
  now available (2 of 9 provinces); full municipality-level ranking still not possible.
- **Data Gap #2** (sales by segment): still open, no change.
- **Data Gap #3** (coal-specific security data): still open; provenance of existing case examples
  fixed, but neither sourced case is coal-specific.
- **Data Gap #4** (long-run history): PARTIALLY CLOSED for municipal debt (2→3 comparable annual
  points; CAGR still correctly suppressed, requires 5). Electricity sales unchanged (still 2 points).

### Added
- `docs/technical_audit.md`, `docs/data_dictionary.md`, `docs/QUALITY_SCORECARD.md` (new in Phase 2)
- `sql/05c_dim_legal_status_and_metric.sql`, `sql/08_fact_security.sql` (replaces
  `08_fact_security_incidents.sql`), `sql/13_source_freshness.sql`
- `tests/test_data_quality.py` — 11 automated tests, executed and passing (verified this session,
  not merely written)
- `.github/workflows/data-integrity.yml` — CI workflow (written and locally-equivalent-verified;
  not yet executed inside live GitHub Actions, since this environment has no push access to a
  real repository)

### Removed / replaced
- `sql/08_fact_security_incidents.sql` (replaced by `sql/08_fact_security.sql`)
- Phase-1 `docs/data_model.md`, `docs/limitations.md`, `docs/kpi_dictionary.md`,
  `reports/eskom_strategic_intelligence_report.md`, `docs/data_source_register.csv` — all rewritten
  in place (not merely patched) to reflect the corrected schema and research.

### Still not implemented (see docs/QUALITY_SCORECARD.md for full detail)
- No `.pbix`/`.pbip` file — this environment cannot run Power BI Desktop.
- CI workflow not executed inside live GitHub Actions (no real repo to push to).
- `scripts/build_project.py` single-command orchestration not yet built.
- Data Gaps #2 and #3 remain open.

---

## [Phase 1] — 2026-09-03
### Added
- Initial repository scaffold (data/, src/, sql/, powerbi/, docs/, reports/, tests/, assets/).
- `docs/data_source_register.csv` with 25 verified entries, all traceable to primary Eskom
  disclosures (FY2026 results, 31 Aug 2026) and the City of Johannesburg/City Power settlement
  (21 Aug 2026), plus one archival SALGA data point (2019) for long-run context only.
- `docs/status_history_municipal_debt.csv` distinguishing the City of Johannesburg's delinquent
  (17 May 2026 PAJA notice) and settled (21 Aug 2026) status — resolved case is NOT shown as
  currently delinquent anywhere in the project.
- `docs/data_model.md` — dimensional model (DimDate, DimMunicipality, DimProvince,
  DimCustomerSegment, DimIncidentType, DimLocation; FactMunicipalDebt, FactElectricitySales,
  FactSecurityIncident) with grain definitions and explicit gap flags.
- `docs/limitations.md` — four documented data gaps (municipality-level arrears table,
  segment-level sales split, coal-specific crime breakdown, pre-FY2025 historical series).
- `docs/kpi_dictionary.md` — every KPI with definition, formula, source, and evidence-type tag.
- `docs/methodology.md` — evidence taxonomy, source hierarchy, causality discipline.
- SQL layer (`sql/01`–`sql/12`): source profiling, data-quality checks, dimension and fact DDL
  with real seed data only, debt-trend/CAGR (guarded against insufficient history), sales
  analysis, Pareto analysis (correctly returns zero rows pending Data Gap #1 closure), and
  executive KPI rollup view.
- `powerbi/dax/measures.dax` — reusable DAX measures, including a guarded `Debt CAGR` measure
  and evidence-type-aware scenario isolation.

### Verified this pass (research date 2026-09-03)
- Eskom FY2026 group results (net profit R30.3bn, municipal arrears R111.6bn/+17.9%, sales
  178TWh/-6.2%, revenue R354.7bn/+4.1%, EAF 65.16%, load shedding 4 days/26 hrs) — source:
  eskom.co.za results announcement, corroborated by Reuters/CNBC Africa, Daily Maverick,
  TechCentral, The Citizen, Ecofin Agency, Briefly.co.za, Rio Times.
- Municipal arrears in-year read of R119.9bn as at June 2026 (management disclosure).
- City of Johannesburg/City Power R5.255bn debt settled in full 21 Aug 2026, PAJA process
  withdrawn — source: eskom.co.za, corroborated by SABC, eNCA, EWN, IOL, BusinessDay,
  MyBroadband, Energize.
- Eskom FY2026 aggregate physical-security crime KPIs (incidents -13%, losses R191m/-18%,
  arrests 505/+18%, recoveries R34m/+38%, convictions 13) — confirmed as an AGGREGATE figure
  across all crime categories, NOT a coal-theft-specific breakdown. This distinction is now
  enforced structurally in the data model (see `docs/data_model.md`), not just noted in prose.

### Known gaps carried forward (see docs/limitations.md)
- Data Gap #1: municipality-level arrears table (blocks debtor ranking, Pareto chart, provincial map)
- Data Gap #2: electricity sales by customer segment (blocks segment YoY decomposition)
- Data Gap #3: coal-theft-specific incident/loss/arrest/conviction figures
- Data Gap #4: pre-FY2025 historical time series (blocks a defensible multi-year CAGR)
- Unverified: the brief's cited "2-3 GW surplus capacity" figure was not located in primary
  sources this pass and is excluded from all outputs pending verification.

### Not yet built (Phase 2+)
- Power BI .pbix file itself (this environment cannot run Power BI Desktop — DAX, data model,
  and Power Query M are provided as source artefacts for direct import).
- Python ingestion scripts in `src/ingestion/` (structure created, scripts pending real API/CSV
  endpoint confirmation for each source).
- Full executive report narrative sections beyond the skeleton in
  `reports/eskom_strategic_intelligence_report.md`.
- `docs/architecture/` diagram, `tests/` data-quality test suite, dashboard screenshots.
