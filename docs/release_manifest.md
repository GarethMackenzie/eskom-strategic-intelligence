# Release Manifest

## Release identity

- Release: v1.0.0 release candidate
- Release date: 9 September 2026
- Release branch: `release/v1-final-hardening`
- Baseline main commit: `ca10118af4db78341e6656fbb2ab47e22ad8754c`
- Release-candidate commit: assigned by Git when this manifest is committed; use the current branch
  HEAD and the pull-request checks as the authoritative candidate identity
- GitHub Actions: PENDING — release-branch checks run on the pull request
- Power BI Desktop model runtime: PASS — Desktop 2.157.1354.0 on 8 September 2026
- Human visual/accessibility inspection: PENDING HUMAN SIGN-OFF
- Power BI Service publication: OUTSIDE REPOSITORY RELEASE SCOPE

No tag or GitHub release is created by this candidate. The proposed release tag is `v1.0.0` only
after pull-request approval, passing CI, and recorded human visual/accessibility sign-off.

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
6. Require passing pull-request CI.
7. Complete and record the five-page human checklist in `POWER_BI_RUNBOOK.md`.

## Recorded runtime result

Power BI Desktop 2.157.1354.0 opened the generated compatibility-level-1606 project on
8 September 2026. All 34 measures reported a valid engine state. A live DAX query returned the
expected headline values, 21 period rows, 29 metric rows, 4 tariff rows, 1 scenario row and 40
source-register rows. This proves model compilation and execution, not final visual or accessibility
sign-off.

## Provenance hardening in this candidate

- DS002, DS004, DS005, DS007, DS010 and DS011: upgraded to the official FY2026 Eskom reporting
  suite after checking metric, period, units and reporting scope.
- DS025: corrected to NERSA's official 87.74c/kWh temporary ferrochrome-smelter relief for calendar
  2026; the unsupported secondary 62c/kWh claim was removed.
- DS027: upgraded to Eskom's direct statement.
- DS013: official evidence confirms four load-shedding days; the 26-hour component remains clearly
  qualified as secondary-only.

## Known boundaries

Complete municipality-level arrears, coal-specific security metrics, long-run sales/EAF history,
final human visual/accessibility inspection and Power BI Service publication remain outside the
automated repository gate. See `limitations.md` and `PRIMARY_SOURCE_UPGRADE_BACKLOG.md`.
