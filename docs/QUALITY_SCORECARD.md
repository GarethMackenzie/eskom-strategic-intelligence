# Quality Scorecard — Phase 4 Release Candidate

Reviewed 7 September 2026. Scores reflect verified repository evidence and a live Power BI Desktop
open, refresh and five-page render. Power BI Service publication remains a separate gate.

| Category | Score /10 | Evidence and remaining limitation |
|---|---:|---|
| Research | 9.0 | 38 governed records across Eskom, NERSA, Treasury, Parliament and corroborating sources. The 8.83% path has primary regulator evidence; its current retail-structure consultation status is secondary pending the official consultation document. |
| Source integrity | 9.5 | Originator, publisher, tier, URLs, status and evidence type are separate. Tariff value and regulatory status have dual-source lineage. One historical debt conflict remains open and visible. |
| Data quality | 10.0 | 11 build-time checks and 27 release tests pass, covering keys, lineage, scenarios, tariff status, freshness, DAX guardrails, PBIP structure, visual layout, privacy and reproducibility. |
| SQL | 9.5 | Every SQL file executes in the declared SQLite target. The model includes dimensional facts, tariff-path logic, window functions, guarded CAGR, QA and analytical views. |
| Data model | 9.5 | Reported actuals, regulatory tariff paths and scenarios are separated. Point-in-time stocks cannot be accidentally summed across time in governed measures. |
| DAX | 9.8 | 30 explicit measures cover debt, tariff, sales, operations, financials, security and governance. Latest-period semantics and the 8.83% regulatory qualification are encoded, tested and executed successfully in Power BI Desktop. |
| Power BI source | 10.0 | Complete `.pbip` with enhanced PBIR report, TMDL semantic model, 5 pages, 68 visuals, slicers and theme. Structural QA passes and all pages render correctly after a clean Desktop refresh. Service publication remains separate. |
| Reproducibility | 10.0 | One command rebuilds the database, QA summary and the deterministic Power BI project; GitHub Actions follows the same path. |
| Documentation | 9.5 | README, runbook, report, audit, source register, data model, methodology, KPI definitions and limitations are cross-linked and status-aware. |
| Executive usefulness | 9.0 | The report integrates tariffs, arrears, demand, EAF, financial performance and governance. Public-data granularity still constrains municipality-level and segment-level actionability. |

**Source- and Desktop-runtime-validated portfolio assessment: 9.7/10.** The repository meets a high
professional standard, its automated release gates pass, and the report has been opened, refreshed
and checked page by page in Power BI Desktop. A literal 10/10 is reserved for a verified Power BI
Service publication with the intended workspace permissions.

## Release gates completed

- Complete SQLite build succeeds and every shipped SQL file executes.
- 11 build-time integrity checks pass.
- 27 pytest release tests pass.
- Complete PBIP/PBIR/TMDL source builds deterministically.
- Five ordered pages, 68 visuals, 30 measures and three relationships pass structural validation.
- Power BI Desktop 2.157.1354.0 opens, refreshes and renders all five pages without errors.
- The 8.83% value retains its regulator source and separate consultation-status source.
- Scenario records do not enter actuals or report freshness.
- Fiscal-year debt measures cannot substitute the June 2026 in-year snapshot.
- No local user paths, external credentials or credential assignments are present in tracked text.

## Final 10/10 Service gates

1. Publish to an authorised Power BI Service workspace.
2. Verify the Service report URL, permissions and interactive rendering.

Until those checks are performed, describe the project as **complete, source-validated and
Desktop-runtime-validated**, not as publicly hosted in Power BI Service.
