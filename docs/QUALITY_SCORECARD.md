# Quality Scorecard - Release Review

Reviewed 4 September 2026. Scores reflect repository evidence, not aspirational capability.

| Category | Score /10 | Evidence and remaining limitation |
|---|---:|---|
| Research | 8.5 | 35 governed records across Eskom, Treasury, NERSA, Parliament and corroborating sources. Some sales and security details remain secondary or unavailable. |
| Source integrity | 9.0 | Originator, publisher, tier, URLs, verification status and evidence type are separate fields. Tier-A URL and evidence-type rules are automated. One historical debt conflict remains unresolved and visible. |
| Data quality | 9.5 | Nine build-time checks and 17 release tests cover keys, lineage, scenarios, freshness, DAX guardrails, source structure and privacy. |
| SQL | 9.0 | One declared target (SQLite); every SQL file executes in the build. Includes dimensional modelling, window functions, trend logic, guarded CAGR, QA and views. Granular source gaps limit some outputs. |
| Data model | 9.0 | Grain and keys are documented; point-in-time stocks and scenarios are protected from unsafe aggregation. |
| DAX | 8.5 | Latest, selected-date and fiscal-year-end debt calculations are separate. Static review and guardrail tests pass; Power BI runtime validation is outstanding. |
| Power BI | 4.0 | DAX and schema artefacts exist, but there is no completed `.pbix` or `.pbip`. No dashboard screenshot is claimed. |
| Reproducibility | 9.5 | `python scripts/build_project.py` builds the database and QA summary; pytest and GitHub Actions use the same code path. |
| Documentation | 9.0 | README, report, audit, source register, data model, dictionaries, methodology and limitations are cross-linked. |
| Executive usefulness | 8.5 | Findings and recommendations are evidence-tagged and avoid causal overclaiming. Municipality- and segment-level data gaps constrain actionability. |

**Overall portfolio assessment: 8.7/10.** The repository is strong analytical-engineering evidence,
with its score capped by the absence of a runtime-validated Power BI artefact and unresolved public
data gaps. Automated repository checks can reach 100% pass; the project itself should not be called
literally flawless while those limitations remain.

## Release gates completed

- Complete SQLite build succeeds.
- All shipped SQL executes.
- Nine build-time integrity checks pass.
- Seventeen pytest tests pass.
- Scenario records do not enter actuals or freshness.
- Fiscal-year debt measures cannot substitute the June 2026 in-year snapshot.
- No local user paths or credential assignments are present in tracked project text.

## Remaining work

1. Build and validate the report in Power BI Desktop, including filter context and displayed totals.
2. Obtain municipality-level debtor balances and customer-segment sales data.
3. Reconcile the FY2024 municipal-arrears source conflict.
4. Obtain a coal-specific security time series before publishing coal-specific metrics.
