# Technical Audit - Repository Review and Release Remediation

**Auditor:** self-review, applying the P0–P3 severity scheme requested for this remediation pass.
**Scope:** every file in the Phase 1 delivery.
**Method:** re-read every file against its own stated intent, re-executed all SQL, checked source
classification against the actual originating organisation of each URL.

Severity: **P0** = factual/data-integrity defect. **P1** = could materially mislead an executive or
hiring manager. **P2** = professional-quality improvement. **P3** = cosmetic/documentation.

---

## P0 — Factual / data-integrity defects

**P0-1. Secondary press URLs classified `A-Primary` in `data_source_register.csv`.**
DS002, DS004, DS005, DS011, DS023, DS024, DS025 all cite `dailymaverick.co.za`, `techcentral.co.za`,
`riotimesonline.com`, `ecofinagency.com` as the `source_url`, yet several were rated
`A-Primary` on the reasoning that "the underlying information originated from Eskom." This
conflates **originating entity** with **publishing entity**. A Daily Maverick paraphrase of a
results-presentation Q&A is not the same evidentiary weight as eskom.co.za's own press release,
even when the number is accurate. **Fix:** rebuilt register (Step 2 below) separates
`originating_entity`, `source_publisher`, and `source_tier` (A1/A2/B/C/UNVERIFIED) as distinct
columns, and every row has been individually re-rated.

**P0-2. `fact_security_case_log` reuses one broad source (DS019, the Sunday Times investigator-
tender article) as the `source_dataset_id` for three unrelated individual cases** (Camden fuel-oil
theft, Tutuka dome-valve theft, and the NATJOINTS R1.09m case cluster) — none of which the tender
article actually reports. The Camden and Tutuka cases were sourced from separate Eskom press
releases in the original research but the file shipped citing the wrong ID. This is a genuine
provenance error: a reviewer clicking through DS019 would not find the case described. **Fix:**
each case now gets its own dataset ID resolving to the actual press release it came from.

**P0-3. `Total Municipal Debt` DAX measure sums `gross_arrears_rand` with no date qualifier beyond
`municipality_key = 0`.** Because `fact_municipal_debt` legitimately holds three group-total rows
for FY2026 alone (FY2025 year-end, FY2026 year-end, June-2026 management disclosure), an
unfiltered card using this measure in Power BI would return R94.6bn + R111.6bn + R119.9bn =
**R326.1bn** — a meaningless sum of three point-in-time stock balances presented as if it were one
current figure. This is exactly the "sum of point-in-time balances shown as current balance"
failure mode data-quality tests are supposed to catch, and the original test suite did not catch
it because it tested row-level integrity, not measure-level aggregation behaviour. **Fix:** replaced
with `Latest Reported Municipal Debt`, filtered to the single most recent non-scenario
`is_fiscal_year_end`-appropriate observation.

**P0-4. `Data As Of Label` DAX measure uses `MAX(dim_date[calendar_date])` over a dimension that
contains a 2031 scenario date.** As shipped, any visual touching `dim_date` without an explicit
scenario exclusion would display "Data as of 31 March 2031" — actively wrong, and the exact failure
mode Step 9 of this brief calls out by name. **Fix:** scenario dates isolated (see P0-5), and a new
`fact_source_refresh` structure drives the freshness label instead of a raw `MAX()` over the date
dimension.

**P0-5. Scenario rows are not physically isolated from the fact table they share with actuals.**
`fact_municipal_debt` carries the FY2031 R358bn scenario row with only an `is_scenario` boolean
flag as protection. Every measure and every ad hoc query must remember to filter it out; nothing
in the schema prevents a future contributor (or a careless DAX `SUM`) from including it. **Fix:**
scenario observations moved to a dedicated `fact_municipal_debt_scenario` table with no shared grain
that a naive `SUM` could accidentally aggregate into.

## P1 — Could materially mislead an executive or hiring manager

**P1-1. `fact_security_incidents` attributes five distinct metrics (incidents, losses, arrests,
recoveries, convictions) — each independently disclosed in the same Eskom press release — to a
single `source_dataset_id` (DS014) via five separate columns on one row.** This works today because
all five happen to come from one release, but it hides the fact that these are five separate
observations, not one, and doesn't generalise (e.g. if a future refresh gets losses from a
different disclosure than arrests). **Fix:** decomposed into `fact_security_metric` at
(reporting_date × incident_scope × metric_key × location_key) grain, one observation per row, each
carrying its own `source_dataset_id`.

**P1-2. `fact_security_case_log.legal_status` contains the value `'Mixed (Arrest+Conviction,
aggregated across cases)'`** — exactly the kind of non-atomic, ambiguous legal-state string this
remediation brief calls out as unacceptable. It also aggregates multiple cases into one row,
destroying case-level traceability. **Fix:** `dim_legal_status` created with a controlled vocabulary
(Allegation/Investigation/Arrest/Charge/Conviction/Sentence/Case Closed); the aggregated NATJOINTS
row split into what can honestly be represented (a metric-level observation, not a case) and moved
out of the case log entirely — see Step 3 detail below.

**P1-3. `docs/data_model.md` describes `FactMunicipalDebt` status semantics ("Delinquent") as if a
single group-total row can meaningfully carry one operational status label.** A R111.6bn group
total is not "delinquent" in the same operational sense a single named municipality is — it's an
aggregate exposure figure. The documented grain also doesn't mention the June-2026 non-year-end
disclosure point as a distinct observation type. **Fix:** grain documentation rewritten (Step 7)
with explicit `observation_type` (Year-End Reported / In-Year Management Disclosure / Event-Driven
Settlement) replacing the misleading single `status` field at group-total grain.

**P1-4. Report language included editorial framing** — "the classic 'sell less, charge more'
pattern utilities fall into" — which is an unattributed generalisation, not a sourced claim.
**Fix:** rewritten in neutral evidence-led language per Step 18.

**P1-5. The original report's single recommendation (Section 9) did not follow the structured
recommendation framework** (problem/evidence/mechanism/impact direction/difficulty/dependencies/
risk/owner/horizon/KPI/data required/confidence) requested in the original brief and repeated here.
**Fix:** rebuilt as a structured table per Step 17, still limited to what current evidence
actually supports (i.e. still short — the honest constraint hasn't changed, only the structure).

## P2 — Professional-quality improvements

- `sql/06_fact_municipal_debt.sql` mixed `ALTER TABLE` (adding `is_scenario`) into the middle of a
  seed script and mixed dimension inserts (the FY2031 scenario date) into a fact script — not
  idempotent, and violates separation of concerns Step 6 flags explicitly. Fixed: dimension inserts
  moved to the dimension layer; scripts rewritten with `IF NOT EXISTS` guards / safe re-run pattern
  appropriate to standard SQL (documented per-statement given no single target engine is assumed).
- `Segment Contribution %` DAX was defined against a dimension with no populated non-aggregate
  rows, so it always returns `BLANK()` — technically not wrong, but untested and unreviewed for
  filter-context correctness as required by Step 11. Now explicitly commented as untestable until
  Data Gap #2 closes, with the filter-context logic reviewed and corrected (previous version did
  not correctly strip only the segment filter — see DAX changes below).
- `Crime Incidents YoY %` DAX summed a pre-computed YoY percentage rather than computing it from
  levels — technically returns the right single number today (one row) but is structurally unsafe:
  it would silently sum percentages across periods if a second period were added. Fixed.

## P3 — Cosmetic / documentation

- KPI dictionary did not consistently state expected filter behaviour per metric (Step 25
  requirement). Being added incrementally; not yet complete for every KPI (see remaining blockers
  in `docs/QUALITY_SCORECARD.md`).
- No ERD image, only prose grain descriptions. A text-based ERD (Mermaid) has been added in this
  pass; a rendered image is not.

---

## Final release remediation - 4 September 2026

The release review found two additional executable defects and corrected them:

- `sql/01_source_profiling.sql` referenced a non-existent `publisher` column and used operators
  that were incompatible with the repository's tested SQLite path.
- `sql/02_data_quality.sql` still referenced retired Phase-1 fields and
  `fact_security_case_log`, so it could not execute against the documented current model.
- Fiscal-year DAX reused the global latest-debt measure. Because that measure deliberately removes
  date filters, it could substitute the June 2026 R119.9bn snapshot for the FY2026 year-end
  R111.6bn balance. A dedicated `Latest Fiscal Year-End Municipal Debt` measure now supplies YoY
  and absolute-change calculations.

The repository now has one declared SQLite target, a standard-library Python loader, a one-command
build, nine build-time checks, 17 pytest tests and a GitHub Actions workflow that compiles Python,
builds the database, executes every SQL file, runs tests and verifies generated outputs.

## What this audit still does not cover

- Power BI Desktop runtime validation or a completed `.pbix`/`.pbip`.
- Closure of the public-data gaps and the FY2024 arrears reconciliation item documented in
  `docs/limitations.md`.
- Any claim that unavailable granular security data is coal-specific.

See `docs/QUALITY_SCORECARD.md` for the scored assessment against this audit.
