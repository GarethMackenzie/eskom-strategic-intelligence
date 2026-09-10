# Final Technical Audit

**Scope:** repository data, sources, SQL, Python, DAX, PBIP/PBIR/TMDL, visuals, documentation,
licensing, CI and local runtime behavior.
**Severity:** P0 factual/data-integrity; P1 materially misleading; P2 engineering quality;
P3 documentation/polish.

## Findings and dispositions

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| FA-01 | P0 | FY2024 total municipal arrears incorrectly shown as R55.3bn | Fixed: official Eskom value R74.4bn |
| FA-02 | P0 | R55.3bn and ~R74bn presented as an unresolved source conflict | Fixed: R55.3bn is programme-approved legacy debt; scopes separated |
| FA-03 | P0 | Only three annual debt points; growth history and CAGR suppressed | Fixed: official FY2015–FY2026 series; dynamic CAGR |
| FA-04 | P0 | PBIP generator duplicated facts already present in SQL | Fixed: generator reads validated `vw_powerbi_*` SQLite views |
| FA-05 | P0 | DAX embedded fixed latest dates and prior values | Fixed: latest/prior period resolution is dynamic |
| FA-06 | P0 | Tariff index embedded decimal rate literals | Fixed: `PRODUCTX` over governed tariff rows |
| FA-07 | P1 | Secondary source used for current NERSA consultation status | Fixed: upgraded to NERSA's official 2 Sep 2026 consultation document |
| FA-08 | P1 | Report freshness asserted a literal date | Fixed: compared to source-derived maximum eligible publication date |
| FA-09 | P1 | EAF values duplicated in a reporting-query CTE | Fixed: dedicated canonical corporate metric fact |
| FA-10 | P1 | Generated DAX could drift from TMDL measure definitions | Fixed: one measure catalog emits both artifacts |
| FA-11 | P1 | Power BI Desktop local metadata appeared as uncommitted changes | Developer-local metadata was excluded; generator outputs were rebuilt independently |
| FA-12 | P2 | CI did not enforce lint, format or clean deterministic rebuild | Fixed: Ruff plus two clean-build gates |
| FA-13 | P2 | Incomplete MIT warranty/liability text and unnamed holder | Fixed |
| FA-14 | P2 | Docs and preview retained obsolete conflict/release-candidate wording | Fixed |
| FA-15 | P0 | Desktop rejected a generated 1600 model as a downgrade from engine level 1606 | Fixed: generator and regression test require 1606 |
| FA-16 | P0 | Desktop marked two measures invalid because `Path` and `FirstDate` are reserved DAX identifiers | Fixed: collision-free variable names; all 34 live measure states valid |

## Canonical data boundary

Business values are authored in governed SQL facts and traced to `docs/data_source_register.csv`.
`sql/15_semantic_exports.sql` exposes a stable interface to Power BI:

- `vw_powerbi_period`
- `vw_powerbi_metric`
- `vw_powerbi_tariff`
- `vw_powerbi_scenario`
- `vw_powerbi_source`

The build order is deliberately one-way:

```text
source register + SQL -> SQLite -> release-blocking QA -> PBIP/PBIR/TMDL/DAX/SVG
```

If any data-quality check fails, Power BI generation is skipped. This prevents a polished artifact
from being regenerated from invalid analytical data.

## Data invariants

The release enforces these invariants in executable checks and tests:

- the annual municipal series has exactly 12 points from FY2015 through FY2026;
- FY2024 total arrears equals R74.4bn;
- R55.3bn exists in the debt-relief programme table and nowhere in the total-arrears fact;
- scenarios never enter actuals or freshness;
- every semantic metric resolves to a registered source;
- point-in-time stock measures use latest/prior rows rather than historical sums;
- tariff values and regulatory status have separate lineage;
- the PBIP generator contains none of the retired value/date literals;
- all report JSON is valid, visual fields resolve, and visuals remain on-canvas without overlap;
- no local user path, credential assignment or PBIX binary is committed.

## Power BI audit

The report remains intentionally compact: five pages, six KPI cards per page, two to four charts,
lineage tables where decision context requires them, persistent interpretation footers, and a
single corporate theme. The full 12-year debt trend now fits the Municipal Debt and Executive
Overview line charts without changing visual binding contracts.

The semantic model has six visible functional tables and three single-direction period
relationships. Scenario data remains physically separate. Auto-recovery is enabled; local `.pbi`
state, `.platform` metadata and `.pbix` binaries are ignored.

The current runtime result is recorded in `docs/POWER_BI_RUNBOOK.md`: Desktop 2.157.1354.0 opened
the final generated model, all 34 measures compiled, and a live DAX query returned the expected
headline values and row counts. This does not replace final human visual/accessibility review at
the target display size.

## Remaining limitations

No P0 or P1 audit item remains open. The remaining constraints are public-data coverage and Power
BI Service publication authority, documented in `docs/limitations.md`.
