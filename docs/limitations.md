# Data Gaps and Limitations

## Closed in the final integrity release

### Municipal arrears history and the R55.3bn scope error

The prior release incorrectly treated R55.3bn as FY2024 total municipal arrears and presented an
apparent conflict with Eskom CFO testimony of approximately R74bn. Primary documents resolve the
issue:

- Eskom's official annual series reports FY2024 municipal and metro arrears of **R74.4bn** and
  FY2025 arrears of **R94.6bn**.
- National Treasury's 2023/24 Annual Report identifies **R55.3bn** as the approved legacy-debt
  amount across 71 Municipal Debt Relief Programme applications, based on the R58.5bn owed at
  31 March 2023.

These are different scopes, not competing estimates. The alternate-estimate table and conflict
language were removed. R55.3bn now lives only in `fact_municipal_debt_relief_programme`; it cannot
appear in the annual total-arrears trend. The official FY2015–FY2026 series closes the long-run
municipal-debt gap and supports a dynamic CAGR.

### FY2027/28 regulatory status

NERSA's own source now replaces the secondary consultation-status source. The model deliberately
separates:

1. the 8.83% estimated average price/revenue path supported by DS035; and
2. the detailed Eskom Retail Tariff Structural Adjustment consultation supported by DS037.

The project does not describe 8.83% as the final increase for every customer category. It remains
subject to the qualifications in the regulator's source material.

## Open data gaps

### 1. Municipality-level arrears

The public evidence supports the national total, two provincial values and a City of Johannesburg
case history. It does not provide a complete municipality-by-municipality balance and payment
history. A national Pareto ranking, municipality risk score or map would therefore imply unsupported
coverage.

Needed: a complete dated municipality table, payment history, Debt Relief Programme status and
consistent entity identifiers from Eskom or National Treasury.

### 2. Electricity sales by customer segment

Only aggregate annual sales are modelled. The 40–44% municipal-share range is contextual and not a
segment-level TWh table. Customer-segment contribution, elasticity and retention analysis remain
blocked until a complete source table is available.

Needed: Eskom sales by category or equivalent NERSA regulatory financial reporting data on a
consistent annual basis.

### 3. Coal-specific security data

Eskom's public FY2026 security disclosure aggregates cable, coal, fuel, illegal connections, meter
tampering, ghost vending, vandalism and sabotage. It does not publish a coal-only incident, loss,
recovery or conviction time series. The Camden and Tutuka case studies concern fuel oil and valves,
respectively; neither is relabelled as coal theft.

Needed: category-level Eskom, SAPS/Hawks, SIU or parliamentary data with incident dates, loss and
recovery values, locations and legal outcomes.

### 4. Long-run sales and EAF history

The municipal-debt history is now complete for FY2015–FY2026, but the model still has only FY2025
and FY2026 comparators for annual electricity sales and EAF. Their YoY measures are valid; long-run
trend or causal claims are not.

## Evidence-quality boundaries

- Exact June 2026 arrears (R119.9bn), FY2026 electricity revenue and several contextual metrics
  still depend on secondary reporting, as flagged in the source register.
- The source register stores publication, retrieval and verification dates separately. Report
  freshness is the latest non-scenario, non-superseded publication date; it is not today's date.
- The FY2031 R358bn value is an Eskom management scenario with no disclosed annual trajectory. It
  is isolated from actuals and is not independently forecast by this project.
- Recommendations are analytical options, not proof of causal impact or implementation authority.
- GitHub validates text-based Power BI source but does not provide Power BI interactivity. Service
  publication requires an authorised workspace and a separate permission decision.
