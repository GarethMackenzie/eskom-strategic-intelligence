# Eskom Strategic Intelligence

**Power BI · Analytics Engineering · Regulatory Intelligence · Data Quality**

[![Data Integrity CI](https://github.com/GarethMackenzie/eskom-strategic-intelligence/actions/workflows/data-integrity.yml/badge.svg)](https://github.com/GarethMackenzie/eskom-strategic-intelligence/actions/workflows/data-integrity.yml)

An executive analytics case study built from governed public evidence on Eskom's municipal debt,
electricity demand, tariffs, financial performance and physical-security risk. It ships as an
editable Power BI Project (`.pbip`), PBIR report, TMDL semantic model, reproducible SQLite model,
Python build pipeline, automated QA and GitHub Actions workflow.

**Latest non-scenario evidence: 2 September 2026.** This date is derived from the source register
during the build. No private customer, employee or operational data is used.

### v1.0.0 release-candidate status

| Gate | Status |
|---|---|
| Automated repository QA | PASS — 17 build checks and 32 tests |
| GitHub Actions | PASS — pull request #1 release-candidate checks |
| Power BI Desktop model runtime | PASS — compatibility level 1606 |
| Human visual/accessibility sign-off | PASS — user-confirmed final review completed |
| Power BI Service publication | Not part of the repository release |

## Dashboard preview

![Eskom Strategic Intelligence Power BI Desktop dashboard](assets/eskom-power-bi-dashboard-screenshot.png)

| Executive KPI | Latest value | Evidence status |
|---|---:|---|
| Year-end municipal arrears | **R111.6bn** | FY2026 official actual |
| Electricity sales | **178 TWh** | FY2026 official actual |
| Energy Availability Factor | **65.16%** | FY2026 official actual |
| Net profit after tax | **R30.3bn** | FY2026 official actual |
| FY2027/28 average price path | **8.83%** | ERTSA structure under consultation |
| Governed sources | **40** | Latest evidence 2 September 2026 |

**Municipal arrears trend, FY2015–FY2026:** `▁▁▁▂▂▃▃▄▅▆▇█` — R5.0bn to R111.6bn.

## Critical correction in this release

The canonical municipal and metro arrears series is now Eskom's official FY2015–FY2026 series:

| FY | Rbn | FY | Rbn | FY | Rbn |
|---:|---:|---:|---:|---:|---:|
| 2015 | 5.0 | 2019 | 19.9 | 2023 | 58.5 |
| 2016 | 6.0 | 2020 | 28.0 | 2024 | **74.4** |
| 2017 | 9.4 | 2021 | 35.3 | 2025 | 94.6 |
| 2018 | 13.6 | 2022 | 44.8 | 2026 | 111.6 |

The previously displayed **R55.3bn is not FY2024 total arrears**. National Treasury identifies it
as the approved legacy-debt scope of 71 Municipal Debt Relief Programme applications, based on
debt at 31 March 2023. That programme-scope fact now lives in a separate table and cannot leak into
the annual total-arrears trend. The June 2026 R119.9bn observation remains a separate in-year
snapshot, and R358bn at FY2031 remains a separate Eskom management scenario.

## Executive snapshot

| Metric | Value | Evidence status |
|---|---:|---|
| FY2026 municipal arrears | R111.6bn | Official year-end actual |
| June 2026 municipal arrears | R119.9bn | In-year observation; separate from year-end |
| FY2015–FY2026 arrears CAGR | Derived in the model | Dynamic first/latest comparator |
| Electricity sales | 178 TWh | Official FY2026 disclosure |
| Energy Availability Factor | 65.16% | Official FY2026 disclosure |
| Net profit after tax | R30.3bn | Official FY2026 disclosure |
| FY2026/27 direct / municipal averages | 8.76% / 9.01% | Implemented |
| FY2027/28 average price path | 8.83% | Average path, not every customer's tariff |
| FY2031 arrears | R358bn | Eskom management no-intervention scenario |

NERSA's 8.83% is modelled as an average price/revenue path. The detailed FY2027/28 Eskom Retail
Tariff Structural Adjustment and customer-category allocation were placed under consultation by
NERSA on 2 September 2026 and are not presented as final category tariffs.

## Architecture

```text
40-record governed public source register
                  |
         SQLite dimensional model
                  |
 17 release-blocking data-quality checks
                  |
 validated semantic export views
                  |
 PBIP generator -> TMDL + PBIR + DAX + SVG + verified PNG fallback
                  |
       5-page Power BI report
```

`scripts/build_project.py` builds SQLite first, runs release-blocking QA, and only then generates
Power BI artifacts from the validated `vw_powerbi_*` views. The generator contains no duplicated
business-fact arrays. One Python measure catalog emits both TMDL measures and the reviewable
`powerbi/dax/measures.dax` export.

## Power BI solution

Open `EskomStrategicIntelligence.pbip` in a current Power BI Desktop release. The project contains:

- 5 pages and 68 visuals;
- 6 semantic-model tables and 3 one-way relationships;
- 34 explicit measures with dynamic latest/prior comparator logic;
- the complete 40-record evidence register;
- separate reported-actual, in-year, tariff-path and scenario structures;
- a portable inline model with no absolute local paths or credentials.

See `docs/POWER_BI_RUNBOOK.md` for the recorded runtime test and Service publication boundary.

## Reproduce the release

Python 3.11 or later is required.

```bash
python -m pip install -r requirements.txt
python -m compileall -q src scripts tests
python -m ruff check src scripts tests
python -m ruff format --check src scripts tests
python scripts/build_project.py
python -m pytest -q
git diff --exit-code
python scripts/build_project.py
git diff --exit-code
```

The last four commands prove that the complete SQL/PBIP build passes, tests pass and a second build
is byte-stable relative to source control. CI runs the same gates on pushes and pull requests.

## Repository guide

| Path | Purpose |
|---|---|
| `EskomStrategicIntelligence.pbip` | Power BI Desktop entry point |
| `EskomStrategicIntelligence.Report/` | PBIR report pages, visuals and theme |
| `EskomStrategicIntelligence.SemanticModel/` | TMDL model, tables, measures and relationships |
| `docs/data_source_register.csv` | Governed provenance register |
| `sql/15_semantic_exports.sql` | Canonical SQLite-to-Power-BI interface |
| `scripts/build_project.py` | Build → QA → Power BI orchestration |
| `scripts/build_powerbi_project.py` | Deterministic artifact generator and measure catalog |
| `tests/` | Data, source, semantic-model, visual and portability tests |
| `reports/eskom_strategic_intelligence_report.md` | Evidence-led strategic report |

## Responsible interpretation

- Point-in-time balances must never be summed across dates.
- Actuals, in-year observations and management scenarios answer different questions.
- Association is not causation; the sales/EAF relationship is descriptive.
- Security metrics are aggregate physical-security disclosures, not coal-specific.
- Municipality-level, customer-segment and coal-specific public data gaps remain explicit.
- Revalidate data and regulatory status before real-world decision use.

Read the [report](reports/eskom_strategic_intelligence_report.md),
[methodology](docs/methodology.md), [data model](docs/data_model.md),
[quality scorecard](docs/QUALITY_SCORECARD.md), [technical audit](docs/technical_audit.md) and
[limitations](docs/limitations.md).
