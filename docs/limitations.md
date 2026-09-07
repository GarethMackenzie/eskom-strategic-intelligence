# Data Gaps and Limitations (Release Review)

## Regulatory status — FY2027/28 8.83% tariff path

NERSA's settlement statement supports an 8.83% estimated final average price impact for FY2027/28
and notes that the figures remain subject to the Regulatory Clearing Account process. Reporting on
4 September 2026 states that the detailed retail tariff structural adjustment and allocation across
customer categories was still open for consultation. The project therefore shows 8.83% as the
average revenue/price path, not as a final tariff for every household, municipality or business.
The current consultation-status source is tier B until the underlying NERSA consultation document
is retrieved. Any Power BI Service publication should refresh this status before use.

## Reconciliation Item #1 — Conflicting municipal arrears figures for FY2024/FY2025 [NEW]
Two credible sources give different figures for the same reporting dates:
- **National Treasury (MTBPS-sourced, DS031, tier B):** R55.3bn (Mar 2024) → R94.6bn (Mar 2025)
- **Eskom CFO Calib Cassim, PMG committee testimony (DS029, tier A1):** approx. R74bn (Mar 2024)
  → approx. R95bn (Mar 2025)

The FY2025 endpoints are close (R94.6bn vs ~R95bn — plausibly the same figure rounded in verbal
testimony). The FY2024 starting points differ by ~R18.7bn, which is not easily explained by
rounding alone. Possible explanations not verified in this pass: different measurement bases
(e.g. total municipal arrears vs. debt-relief-programme-participant arrears only — the PMG context
was a briefing specifically about the Debt Relief Amendment Bill, which may mean Cassim's figure
scopes to programme participants), a timing difference within March 2024, or an inconsistency in
one of the two sources. **This project does not pick a winner.** `fact_municipal_debt` uses the
Treasury/MTBPS figure (because it independently corroborates Eskom's own disclosed FY2026 growth
rate via back-calculation); the PMG figure is preserved in a separate
`fact_municipal_debt_alternate_estimate` table so a reviewer can see both. Next step: retrieve the
specific PMG committee minutes in full (not just the search snippet) and Treasury's own MTBPS
document to determine whether the two figures are measuring the same thing.

## Data Gap #1 — Municipality-level Eskom arrears — PARTIALLY CLOSED
**Original gap:** no municipality-by-municipality breakdown, blocking Pareto/ranking/map.
**Phase 2 progress:** located a **provincial-level** breakdown (Mpumalanga R30.5bn highest, Free
State R29.1bn second — DS030), and a genuine individual-municipality case (City of Johannesburg,
carried since Phase 1). This is enough for a partial provincial-concentration view
(`fact_municipal_debt_provincial`) but **not** a full municipality-level Pareto/ranking — the
source names only the top 2 of 9 provinces, and no municipality-level amounts beyond City of
Johannesburg were located.
**Still needed:** a complete provincial table (7 provinces still unreported) and any individual
municipality's balance beyond City of Johannesburg. National Treasury's Local Government Database
and Eskom's Integrated Report debtor schedule remain the most likely primary sources; not yet
retrieved directly (only reported via secondary coverage of MTBPS/PMG sessions).

## Data Gap #2 — Electricity sales by customer segment — STILL OPEN
No change from Phase 1. Segment-level TWh figures were not located in either research pass. Only
the aggregate 178 TWh (FY2026) / 189.7 TWh (FY2025) and the 40-44% municipal-share estimate exist.
**Next step unchanged:** Eskom's FY2026 Integrated Report sales-by-category table; NERSA
Regulatory Financial Reporting disclosures.

## Data Gap #3 — Coal-specific security data — STILL OPEN (structurally addressed differently)
No coal-specific aggregate time series was located in either pass. Phase 2 corrected a real
provenance defect here (see `docs/technical_audit.md` P0-2): two individual, genuinely-sourced
cases now exist (Camden Power Station fuel-oil theft, Tutuka Power Station valve theft) plus one
metric-level aggregate observation (the NATJOINTS R1.09m cluster). Neither individual case is
coal-specific (one is fuel-oil, one is valve/equipment), which is itself informative: it means this
project has NOT found a properly-sourced coal-specific incident to date, not that coal incidents
don't exist — Eskom's own investigator-tender article (DS019) confirms coal theft/diversion/
adulteration are named, current risk categories, just without a quantified public series.
**Next step unchanged:** SAPS/Hawks and SIU published reports; Parliamentary Portfolio Committee on
Electricity and Energy briefing documents (the PMG site proved fruitful for municipal-debt material
in this pass and is worth searching specifically for coal/security topics next).

## Data Gap #4 — Long-run municipal debt / sales history — PARTIALLY CLOSED (debt only)
**Original gap:** only 2 comparable annual points for municipal debt.
**Phase 2 progress:** now 3 fiscal-year-end points (FY2024 R55.3bn, FY2025 R94.6bn, FY2026
R111.6bn) — still short of the 5 points needed for a defensible CAGR (both SQL and DAX correctly
continue to suppress the CAGR calculation and return a data-sufficiency message rather than a
number computed on 3 points).
**Electricity sales:** still only 2 comparable points (FY2025, FY2026) — no earlier annual sales
figures were located in this pass. Still open.
**Next step:** Eskom's FY2021–FY2023 annual/integrated reports for both series.

## General limitation
Sourcing quality varies meaningfully by topic. The 31 August 2026 Eskom release provides primary
support for EAF, sales volume, profit, aggregate security metrics, capex guidance, the R358bn debt
projection and the estimated 2-3 GW surplus capacity. Exact revenue, exact June arrears and some
coal-crime context still depend on secondary reporting. This unevenness is
reflected honestly in `docs/data_source_register.csv`'s per-row tiering rather than smoothed over.

Every figure carries a `retrieval_datetime`; any dashboard or report generated from this project
must display "Data reported as of [date]" (via `fact_source_refresh` / the `Data Reported As Of`
DAX measure — see `docs/technical_audit.md` P0-4) and should be re-validated once Eskom's FY2026
Integrated Report and Annual Financial Statements are formally published.

GitHub stores and validates the editable PBIP/PBIR/TMDL source, but does not render Power BI
interactivity. A browser-interactive version requires an authorised Power BI Service publication.
Desktop open/refresh/interaction and Service permissions remain separate manual runtime gates; see
`docs/POWER_BI_RUNBOOK.md`.
