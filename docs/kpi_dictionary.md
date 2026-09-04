# KPI Dictionary (Release Review)

Every KPI is tagged by evidence type: **FACT_REPORTED**, **CALCULATION_DERIVED**,
**INTERPRETATION_ONLY**, **SCENARIO_MANAGEMENT**, **SCENARIO_PROJECT**. Each entry below also
states **expected filter behaviour** — how the measure should respond to date/segment/municipality
slicers in Power BI — per Step 25's explicit requirement. This is new in Phase 2; Phase 1's
dictionary did not specify filter behaviour.

---

### Latest Reported Municipal Debt
- **Business definition:** The most recent group-total municipal arrears balance Eskom has disclosed, regardless of report-level date filters.
- **Evidence type:** FACT_REPORTED
- **Calculation:** `MAX(date_key)` for `municipality_key=0`, then the balance at that date. Uses `ALL(dim_date)` to deliberately ignore the report's date slicer — see Expected filter behaviour.
- **Unit:** Rand
- **Grain:** One observation per date_key
- **Source:** DS001 (latest currently: DS002, R119.9bn, June 2026)
- **Frequency:** Ad hoc (whenever Eskom discloses)
- **Owner/stakeholder:** Group CFO / Municipal Debt Management
- **Limitations:** Fixes the Phase-1 P0-3 bug where an unfiltered SUM returned a meaningless total of unrelated snapshots (R326.1bn in Phase 1's 3-row state; R381.4bn now with 4 rows).
- **Expected filter behaviour:** Card visuals with NO date slicer → always shows the single latest known figure. If placed on a page WITH a date slicer, this measure still ignores it by design (that's what "Latest" means) — use `Municipal Debt at Selected Date` instead on pages where the slicer should control the value shown.

### Municipal Debt at Selected Date
- **Business definition:** The municipal debt balance as at whatever date context the report page/slicer provides.
- **Evidence type:** FACT_REPORTED
- **Calculation:** `MAX(date_key)` WITHIN the active filter context (no `ALL()` override).
- **Expected filter behaviour:** Responds to date slicers/bookmarks. On a page with a "FY2026 year-end" bookmark active, returns R111.6bn, not R119.9bn.

### Municipal Debt YoY %
- **Type:** CALCULATION_DERIVED
- **Formula:** `(Latest year-end balance − Prior year-end balance) / Prior year-end balance`, both restricted to `is_fiscal_year_end = TRUE` so the June-2026 in-year disclosure never enters either side of the calculation.
- **Result:** 17.9% (FY2025→FY2026), consistent with Eskom's own disclosed rate.
- **Expected filter behaviour:** Unaffected by municipality/segment slicers (group-total only); a year slicer changes which "current" year-end is used as the numerator.

### Municipal Debt CAGR
- **Type:** CALCULATION_DERIVED
- **Formula:** `(Last value / First value)^(1/(years-1)) − 1` over ACTUAL (non-scenario) fiscal-year-end observations only.
- **Data sufficiency guard:** Returns BLANK() below 5 comparable annual points. **Currently BLANK — 3 points available (FY2024, FY2025, FY2026).** Paired with `Municipal Debt Data Sufficiency Status`, which returns a human-readable explanation string.
- **Expected filter behaviour:** Ignores date slicers (uses full available history by design); would need explicit redesign if a "CAGR over the selected window" behaviour is ever wanted.

### Municipal Debt Scenario (No Intervention, FY2031)
- **Type:** SCENARIO_MANAGEMENT
- **Definition:** Eskom's own stated base case absent intervention.
- **Source:** DS003 (R358bn)
- **Expected filter behaviour:** Lives in a physically separate table (`fact_municipal_debt_scenario`); cannot be affected by any filter context touching `fact_municipal_debt`. **Must only appear on "05 | Scenario & Decision Lab" with the persistent "SCENARIO — NOT MANAGEMENT FORECAST" label.**

### Latest Electricity Sales TWh / Prior-Year Electricity Sales TWh / Sales YoY %
- **Type:** FACT_REPORTED / CALCULATION_DERIVED
- Same LATEST-resolution pattern as the debt measures, applied to `fact_electricity_sales` at `segment_key=0`.
- **Result:** 178 TWh (FY2026), −6.2% YoY.
- **Expected filter behaviour:** A segment slicer would currently return BLANK for any segment other than "ALL SEGMENTS," since no non-aggregate segment rows are populated (Data Gap #2).

### Revenue per kWh
- **Type:** CALCULATION_DERIVED
- **Formula:** `Latest revenue_rand / (Latest sales_twh × 10^9)`
- **Result:** ≈R1.99/kWh, blended across all customer segments.
- **Expected filter behaviour:** Do not present this figure filtered to a segment — it is only valid at the ALL-SEGMENTS grain until Data Gap #2 closes.

### Segment Contribution %
- **Type:** CALCULATION_DERIVED
- **Formula (corrected in Phase 2 — see technical_audit.md P2):** `SUM(sales_twh) [current segment/date filter] / SUM(sales_twh) [ALL-SEGMENTS row, same date filter]`. Fixed to strip only the segment filter via `REMOVEFILTERS(dim_customer_segment)`, not the date filter.
- **Expected filter behaviour:** Should vary correctly by segment once populated; currently returns BLANK for all segments (Data Gap #2) because there is nothing to divide.

### Latest Security Estimated Loss / Latest Security Recoveries / Security Recovery Rate
- **Type:** FACT_REPORTED / CALCULATION_DERIVED
- **Definition:** Eskom's aggregate physical-security crime metrics — **NOT coal-specific.**
- **Source:** DS015 (loss), DS017 (recoveries)
- **Result:** R191m loss, R34m recoveries, ≈17.8% recovery rate, all FY2026 aggregate.
- **Expected filter behaviour:** An `incident_type_key` slicer set to anything other than "0 — AGGREGATE" will currently return BLANK, because no category-specific metric-level rows exist (Data Gap #3). This is deliberate — it prevents a dashboard from ever showing a fabricated "coal loss" figure by falling back to the aggregate value under a coal filter.

### Crime Incidents YoY %
- **Type:** FACT_REPORTED (the percentage itself is Eskom-disclosed, not derived by this project)
- **Fixed in Phase 2:** no longer SUMs a percentage column across periods (see technical_audit.md P2) — resolves to the single latest observation for `metric_key=1`.
- **Expected filter behaviour:** Single value per period; a multi-year trend visual using this measure would need a matrix/line chart with `reporting_date_key` on an axis, not a SUM aggregation across years.

### Data Reported As Of / Data Last Refreshed / Data Freshness Label
- **Type:** N/A (metadata, not a business KPI)
- **Fixed in Phase 2 (P0-4):** no longer `MAX(dim_date[calendar_date])`, which could resolve to the 2031 scenario horizon. Now sourced from `fact_source_refresh`, which structurally excludes scenario dataset IDs.
- **Expected filter behaviour:** Should be placed in a report-wide header/footer, unaffected by page-level filters, so it always reflects the true overall freshness of the dataset regardless of what the user is currently viewing.

### Estimated Excess Generation Capacity
- **Type:** FACT_REPORTED (management estimate)
- **Source:** DS034, direct Eskom release dated 31 August 2026.
- **Reported value:** Estimated 2–3 GW surplus generation capacity.
- **Usage constraint:** Contextual only. It is not modelled as a live operational KPI because no
  dated, metered capacity series is available in this repository. Do not present it as an
  instantaneous surplus measurement.
