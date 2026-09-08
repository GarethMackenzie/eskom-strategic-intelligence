# Release Manifest

## Identity

- Release: Final integrity release
- Date: 8 September 2026
- Branch: `codex/final-integrity-audit`
- Baseline main commit: `2233ce630e768b1ed1cf772054d9400be318e956`
- Preserved pre-audit Desktop state: `stash@{0}`

## Generated Power BI inventory

- Entry point: `EskomStrategicIntelligence.pbip`
- PBIR pages: 5
- PBIR visuals: 68
- TMDL tables: 6
- Relationships: 3
- Explicit measures: 34
- Governed sources: 40
- Canonical export views: 5

## Critical facts

- FY2024 total municipal and metro arrears: R74.4bn (DS038)
- Municipal Debt Relief Programme approved legacy debt: R55.3bn across 71 approvals (DS039)
- FY2026 year-end arrears: R111.6bn
- June 2026 in-year arrears: R119.9bn, kept separate
- FY2031 R358bn: management scenario, kept separate
- FY2027/28 8.83%: average price/revenue path; detailed ERTSA under consultation (DS035/DS037)

## Build contract

1. Build all SQLite facts and views.
2. Run 17 release-blocking checks.
3. Generate TMDL, PBIR, DAX and SVG only on PASS.
4. Run the full pytest suite.
5. Run Ruff lint and format checks.
6. Rebuild twice and require no tracked difference.
7. Open this exact PBIP in Power BI Desktop and record the result in `POWER_BI_RUNBOOK.md`.
8. Push and confirm the GitHub Actions result before declaring GitHub release status complete.

## Recorded runtime result

Power BI Desktop 2.157.1354.0 opened the generated compatibility-level-1606 project on
8 September 2026. All 34 measures reported a valid engine state. A live DAX query returned the
expected headline values, 21 period rows, 29 metric rows, 4 tariff rows, 1 scenario row and 40
source-register rows. Human visual/accessibility sign-off and Power BI Service publication remain
separate release-owner actions.

## Source documents added/upgraded

- DS038: Eskom State of the System Winter Outlook, 22 April 2026 — canonical annual debt series.
- DS039: National Treasury Annual Report 2023/24 — R55.3bn programme scope.
- DS037: NERSA official FY2027/28 ERTSA consultation document — regulatory status.

## Known boundaries

Complete municipality-level arrears, segment-level electricity sales, coal-specific security data,
long-run sales/EAF history and Power BI Service publication remain outside this release's public
data or authorisation boundary. See `limitations.md`.
