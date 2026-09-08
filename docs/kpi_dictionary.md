# KPI Dictionary

The executable measure catalog is in `scripts/build_powerbi_project.py`. It generates both TMDL
and `powerbi/dax/measures.dax`; this document describes business behavior and interpretation.

## Municipal debt

### Latest Year-End Municipal Arrears

- **Type:** FACT_REPORTED
- **Definition:** value at the maximum period containing `Municipal Arrears - Year End`.
- **Current value:** R111.6bn at FY2026.
- **Behavior:** deliberately removes report period filters and resolves the latest governed annual
  stock; it never sums balances across dates.

### Prior Year-End Municipal Arrears

- **Type:** FACT_REPORTED comparator
- **Definition:** value at the maximum year-end period strictly earlier than the latest period.
- **Current value:** R94.6bn at FY2025.
- **Behavior:** selected dynamically; no date or value literal is embedded.

### Municipal Arrears YoY %

- **Type:** CALCULATION_DERIVED
- **Formula:** `(latest year-end − prior year-end) / prior year-end`.
- **Current result:** approximately 18.0%.
- **Constraint:** June 2026 in-year arrears cannot enter either comparator.

### Municipal Arrears Long-Run CAGR

- **Type:** CALCULATION_DERIVED
- **Formula:** `(latest / earliest)^(1 / elapsed years) − 1`.
- **Window:** earliest and latest comparable annual rows, currently FY2015–FY2026.
- **Behavior:** the first date, last date and elapsed years are derived from filter-safe annual data.

### Latest In-Year Municipal Arrears

- **Type:** FACT_REPORTED
- **Current value:** R119.9bn at June 2026.
- **Constraint:** kept separate from annual actuals and never substituted into YoY/CAGR.

### Scenario Municipal Arrears FY2031 / Scenario Gap vs Latest

- **Type:** SCENARIO_MANAGEMENT / CALCULATION_DERIVED
- **Current scenario:** R358bn under Eskom's no-further-intervention case.
- **Constraint:** physically isolated in `FactScenario`; not an actual and not a project forecast.

## Operations and financials

### Latest / Prior Electricity Sales and Sales YoY %

- **Type:** FACT_REPORTED / CALCULATION_DERIVED
- **Current values:** 178 TWh vs 189.7 TWh; approximately −6.2%.
- **Behavior:** latest and prior periods are selected dynamically from `FactMetric`.
- **Limitation:** aggregate only; segment analysis is not supported.

### Latest / Prior EAF and EAF Change pp

- **Type:** FACT_REPORTED / CALCULATION_DERIVED
- **Current values:** 65.16% vs 60.6%; +4.56 percentage points.
- **Behavior:** latest and prior observations are dynamically selected.
- **Interpretation:** association with sales change is descriptive, not causal.

### Net Profit After Tax / Electricity Revenue

- **Type:** FACT_REPORTED
- **Current values:** R30.3bn and R354.7bn.
- **Evidence caveat:** the revenue row retains its secondary-source quality flag.

## Physical security

### Security Losses / Recoveries / Recovery Rate / Arrests / Convictions

- **Type:** FACT_REPORTED / CALCULATION_DERIVED
- **Current values:** R191m losses, R34m recoveries, 505 arrests and 13 convictions.
- **Scope:** aggregate physical security. These measures must never be labelled coal-specific.
- **Unit rule:** percentage-change rows are not added across periods.

## Tariffs

### Tariff Increase %

- **Type:** FACT_REPORTED
- **Behavior:** returns the governed average for the active tariff row.

### FY2026/27 Direct / Municipal Increase

- **Current values:** 8.76% direct from 1 April 2026; 9.01% municipal bulk from 1 July 2026.
- **Behavior:** each measure finds the latest row for its customer-group type; the date/value is not
  embedded in the expression.

### FY2027/28 Average Increase

- **Current value:** 8.83% estimated average price/revenue path.
- **Status:** detailed ERTSA structure and customer-category allocation under NERSA consultation
  from 2 September 2026.
- **Constraint:** not a final tariff for every customer; DS035 supports the value and DS037 the
  consultation status.

### Illustrative Tariff Index

- **Type:** CALCULATION_DERIVED
- **Formula:** baseline 100 multiplied by `PRODUCTX(1 + IncreasePct / 100)` over governed direct and
  average-path rows.
- **Constraint:** an arithmetic index, not a customer bill forecast. No tariff decimal is hardcoded.

## Governance

### Governed Source Count / Primary Source Count

- **Current source count:** 40.
- **Primary definition:** source tier A1 or A2.
- **Behavior:** both derive directly from the embedded `SourceRegister`.

### Latest Evidence Date

- **Definition:** maximum publication date among non-scenario, non-superseded sources.
- **Current result:** 2 September 2026.
- **Constraint:** not derived from scenario dates, retrieval time or today's date.
