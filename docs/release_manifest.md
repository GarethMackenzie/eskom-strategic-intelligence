# Release Manifest

## Release identity

- Target release: `v1.0.0`
- Release readiness date: 10 September 2026
- Documentation branch: `docs/final-readme-release-polish`
- Baseline main commit for this documentation pass: `64300563f716ec9298e76169fc92a872076b4e88`
- GitHub release status: **READY FOR MANUAL PUBLICATION, NOT YET PUBLISHED**
- Power BI Desktop model runtime: PASS, Desktop 2.157.1354.0 on 8 September 2026
- Human visual/accessibility inspection: PASS, user-confirmed final review completed
- Power BI Service publication: OUTSIDE REPOSITORY RELEASE SCOPE

The `v1.0.0` tag and GitHub release must point to the final `main` commit after this documentation
pass is merged and Data Integrity CI succeeds on that exact commit. This manifest does not claim a
GitHub release before it exists.

The root `LICENSE` contains canonical MIT text. GitHub has previously reported `Other` /
`NOASSERTION` for repository licence metadata, so the legal text is left unchanged rather than
modified to influence detection.

## Reproducible inventory

- Entry point: `EskomStrategicIntelligence.pbip`
- PBIR pages: 5
- PBIR visuals: 68
- TMDL tables: 6
- Relationships: 3
- Explicit measures: 34
- Governed sources: 40
- Canonical export views: 5
- Tabular compatibility level: 1606

## Critical facts protected

- FY2024 total municipal and metro arrears: R74.4bn (DS038)
- Municipal Debt Relief Programme approved legacy debt: R55.3bn across 71 approvals (DS039)
- FY2026 year-end arrears: R111.6bn
- June 2026 in-year arrears: R119.9bn, kept separate
- FY2031 R358bn: management scenario, kept separate
- FY2027/28 8.83%: average price/revenue path, not a final customer-category tariff

## Build contract

1. Build SQLite facts and semantic export views from governed source data.
2. Require all 17 release-blocking data checks to pass.
3. Generate TMDL, PBIR, DAX and preview assets only after QA passes.
4. Run all 32 pytest tests and Ruff lint/format checks.
5. Rebuild twice and require zero tracked difference.
6. Require passing GitHub Actions on the final `main` commit.
7. Keep the completed five-page human checklist recorded in `POWER_BI_RUNBOOK.md`.

## Recorded runtime result

Power BI Desktop 2.157.1354.0 opened the generated compatibility-level-1606 project on
8 September 2026. All 34 measures reported a valid engine state. A live DAX query returned the
expected headline values, 21 period rows, 29 metric rows, 4 tariff rows, 1 scenario row and 40
source-register rows.

The final five-page visual and accessibility review was subsequently completed and is recorded as
PASS in `POWER_BI_RUNBOOK.md`.

## Provenance hardening

- DS002, DS004, DS005, DS007, DS010 and DS011 were upgraded to the official FY2026 Eskom reporting
  suite after checking metric, period, units and reporting scope.
- DS025 was corrected to NERSA's official 87.74c/kWh temporary ferrochrome-smelter relief for
  calendar 2026. The unsupported secondary 62c/kWh claim was removed.
- DS027 was upgraded to Eskom's direct statement.
- DS013 uses official evidence for four load-shedding days. The 26-hour component remains clearly
  qualified as secondary-only.

## Manual publication procedure

After this documentation pass reaches `main` and Data Integrity CI succeeds on the resulting SHA:

1. Create tag `v1.0.0` from that exact `main` commit.
2. Create GitHub release **Eskom Strategic Intelligence v1.0.0** from the same tag.
3. State that the release includes the source-controlled PBIP/PBIR/TMDL project, 34 explicit DAX
   measures, 40 governed sources, 17 release-blocking checks, 32 automated tests, 5 report pages and
   68 visuals.
4. Record the completed Power BI Desktop runtime validation and human visual/accessibility review.
5. Describe the R74.4bn / R55.3bn source-scope correction and the separation of actuals, in-year
   observations, regulatory paths and management scenarios.
6. Do not claim Power BI Service publication.

## Known boundaries

Complete municipality-level arrears, coal-specific security metrics, long-run sales/EAF history and
Power BI Service publication remain outside the automated repository gate. See `limitations.md` and
`PRIMARY_SOURCE_UPGRADE_BACKLOG.md`.
