# Methodology

## Evidence taxonomy
Every claim in this project is tagged as one of:
- **FACT** — directly stated by a cited primary or corroborated secondary source.
- **CALCULATION** — derived from cited FACT inputs with the formula shown (e.g. YoY %, revenue per kWh).
- **INTERPRETATION** — an analytical reading of FACTs/CALCULATIONS, explicitly presented as such.
- **SCENARIO** — a conditional output of stated assumptions (Eskom's own or this project's), never a prediction of what will happen.
- **RECOMMENDATION** — a proposed management action, classified further as Evidence-supported existing intervention / Analytically supported recommendation / Proposal requiring pilot.

## Source hierarchy
1. Eskom primary disclosures (results announcements, press releases, integrated reports)
2. Other primary institutions: National Treasury, NERSA, Stats SA, SAPS/Hawks, SIU, Parliament, Auditor-General
3. Corroborating secondary reporting (Reuters/CNBC Africa, Daily Maverick, TechCentral, business press) — used to (a) corroborate a primary figure appearing in multiple outlets' coverage of the same disclosure event, or (b) surface a primary event (e.g. a settlement announcement) that is then verified against Eskom's own release.
Secondary sources never silently replace a primary figure; where only secondary sources exist, the data_quality_rating column flags this explicitly (rating C).

## Causality discipline
Where sales decline and rising self-generation/efficiency/plant-availability trends are discussed
together, the language used throughout this project is "associated with," "consistent with," or
"coincided with" — never "caused by" — unless a specific regression or causal-inference methodology
is applied and documented. Section "Demand Analytics" in the report is explicit that the observed
sales-decline-alongside-availability-improvement pattern is a diagnostic observation, not a proven
causal chain.

## Handling of resolved vs. current cases
Any debtor position that has been settled (currently: City of Johannesburg/City Power, settled
2026-08-21) is carried through a status-history table (`docs/status_history_municipal_debt.csv`)
rather than a single mutable balance field, so historical exposure and current exposure are always
distinguishable. Dashboards must always resolve to the latest status as of the report's stated
"Data as of" date.

## Handling of unverifiable or insufficiently granular claims
Claims that cannot be independently verified are excluded from KPI and chart outputs or retained
with an explicit verification warning. The 2-3 GW surplus-capacity statement is now verified to a
direct Eskom release (DS034), but remains contextual because it is an estimate rather than a dated,
metered operational series.

## Statistical method selection
Methods are chosen only where they answer a specific business question and the underlying data
supports them:
- **YoY % / CAGR** — trend velocity. Debt YoY uses the latest and immediate prior fiscal-year-end
  values; debt CAGR uses the earliest and latest of 12 comparable FY2015–FY2026 observations.
- **Pareto/concentration** — debtor concentration, currently non-executable pending Data Gap #1 (see sql/11_pareto_analysis.sql, which is designed to activate automatically once real data lands).
- **Correlation (not causal)** — used only where two independently sourced series exist for the same period (e.g. sales volume vs. Energy Availability Factor), and always labelled as association, not causation.
- **Scenario/sensitivity analysis** — used for the What-If Municipal Debt and Demand scenarios on the Scenario & Decision Lab page, always labelled as such.

## Refresh model
"Live" is interpreted as "refreshable when the underlying publisher updates," not real-time
telemetry. Eskom results announcements occur roughly twice yearly (interim + annual); municipal
settlement events and security-incident case reports are published ad hoc. The semantic layer
therefore carries both `last_refresh_datetime` (when this pipeline last ran) and
`source_reporting_date` (when the underlying figure was actually as-of), and every dashboard
surfaces publication-date freshness from the governed `SourceRegister`. Scenarios and superseded
records are excluded. Build-time QA derives the expected maximum eligible date from the same
register rather than comparing to a literal release date.

## Canonical data and semantic generation

Business facts are stored once in SQLite facts. After QA passes, `sql/15_semantic_exports.sql`
provides stable `vw_powerbi_*` views that the PBIP generator embeds into TMDL. DAX measures have one
catalog in `scripts/build_powerbi_project.py`; both TMDL and `powerbi/dax/measures.dax` are generated
from it. This prevents SQL/Python/Power BI value drift.
