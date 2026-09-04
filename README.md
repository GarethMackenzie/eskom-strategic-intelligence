# Eskom Strategic Intelligence

**Public-data analytics case study: municipal debt, electricity demand and physical-security risk**

[![Data Integrity CI](https://github.com/GarethMackenzie/eskom-strategic-intelligence/actions/workflows/data-integrity.yml/badge.svg)](https://github.com/GarethMackenzie/eskom-strategic-intelligence/actions/workflows/data-integrity.yml)

This portfolio project turns public disclosures from Eskom, National Treasury, NERSA, Parliament
and related institutions into a governed analytical model. It demonstrates source evaluation,
SQLite modelling, Python automation, data-quality testing, DAX design and executive decision
support. It contains no private customer, employee or operational data.

**Data reported as of 31 August 2026. Pipeline reviewed 4 September 2026.** Forward guidance and
scenarios are physically separated from reported actuals.

## Executive snapshot

| Metric | Reported value | Context | Evidence |
|---|---:|---:|---|
| Municipal arrears, latest exact figure | R119.9bn | June 2026 | Secondary exact figure; official release says approximately R119bn |
| Municipal arrears, year-end | R111.6bn | +17.9% YoY | Official Eskom disclosure |
| Electricity sales | 178 TWh | -6.2% YoY | Official Eskom disclosure |
| Electricity revenue | R354.7bn | +4.1% YoY | Secondary reporting of results presentation |
| Net profit after tax | R30.3bn | Second consecutive profit | Official Eskom disclosure |
| Energy Availability Factor | 65.16% | Up from 60.6% | Official Eskom disclosure |
| Physical-security losses | R191m | -18% YoY; aggregate, not coal-specific | Official Eskom disclosure |
| Municipal arrears projection | R358bn by FY2031 | No-intervention management scenario | **Scenario, not reported actual** |

## What the analysis shows

- Point-in-time municipal debt must be resolved to one dated observation; summing historical
  balances would produce a meaningless R381.4bn total.
- The latest in-year debt figure (R119.9bn) and the latest fiscal-year-end figure (R111.6bn) answer
  different questions. The DAX layer keeps them separate.
- Sales fell while plant availability improved. The report treats this as an association, not a
  causal finding.
- Public evidence supports aggregate physical-security metrics, but not a coal-specific loss or
  incident series. The model does not relabel aggregate figures as coal data.
- Two credible sources conflict on the FY2024 municipal-arrears baseline. Both are preserved and
  the reconciliation item remains open.

## Architecture

```text
Public source register (35 governed records)
                  |
          Python CSV ingestion
                  |
     SQLite dimensions and facts
                  |
  QA rules + 17 automated tests
                  |
 SQL analysis and reporting views
                  |
     DAX semantic-layer measures
                  |
 Executive report / future Power BI model
```

`python scripts/build_project.py` loads the source register, executes every SQL file, builds
`data/processed/eskom_intelligence.sqlite`, runs nine release-blocking integrity checks and writes
`data/processed/qa_summary.json`. Generated files are ignored by Git.

## Engineering controls

- Source lineage at observation grain through `source_dataset_id`
- Separate reported-actual and scenario fact tables
- Atomic evidence classifications and source-tier checks
- Explicit latest-observation and fiscal-year-end DAX measures
- Scenario-safe report freshness derived from actual disclosures only
- Idempotent SQLite DDL and seed scripts
- Reproducible Python build using standard-library ingestion
- Pytest suite covering schema, lineage, DAX guardrails, source integrity and privacy
- GitHub Actions on push, pull request and manual dispatch

## Repository guide

| Path | Purpose |
|---|---|
| `src/` | CSV ingestion, database build and validation package |
| `scripts/build_project.py` | One-command project build |
| `sql/` | Staging, dimensional model, facts, QA and analytical views |
| `tests/test_data_quality.py` | 17 release tests |
| `powerbi/dax/measures.dax` | Reviewed semantic-layer measures |
| `docs/data_source_register.csv` | 35-record evidence and provenance register |
| `docs/` | Data model, dictionaries, audit, methodology and limitations |
| `reports/` | Evidence-tagged strategic intelligence report |

## Run locally

Python 3.11 or later is required.

```bash
python -m pip install -r requirements.txt
python scripts/build_project.py
python -m pytest -q
```

Expected result: nine build-time checks pass and 17 pytest tests pass.

## Power BI status

The star schema and DAX measures are ready for implementation, but this repository does **not**
contain a completed `.pbix` or `.pbip`. The measures have been statically reviewed and protected by
automated guardrail tests; they have not been validated in the Power BI Desktop engine. See
[`docs/QUALITY_SCORECARD.md`](docs/QUALITY_SCORECARD.md) for the remaining manual validation work.

## Responsible interpretation

- The project is a portfolio-grade analytical case study, not an Eskom operational system.
- Forecasts, scenarios and recommendations are not presented as reported facts.
- Association is not presented as causation.
- Unresolved source conflicts and unavailable granular data remain visible.
- Dates, definitions and source quality should be revalidated before any real decision use.

Read the [full report](reports/eskom_strategic_intelligence_report.md),
[methodology](docs/methodology.md), [data model](docs/data_model.md) and
[limitations](docs/limitations.md).
