# Data Dictionary

Column-level reference for every table in the release-reviewed schema. See `docs/data_model.md`
for grain/relationship documentation and `docs/kpi_dictionary.md` for business-metric definitions.

## dim_date
| Column | Type | Notes |
|---|---|---|
| date_key | INTEGER PK | YYYYMMDD |
| calendar_date | DATE | |
| fiscal_year | INTEGER | Eskom FY runs 1 Apr–31 Mar |
| fiscal_year_label | VARCHAR(6) | e.g. 'FY2026' |
| is_fiscal_year_end | BOOLEAN | TRUE only for 31 March closes |
| is_scenario_horizon | BOOLEAN | TRUE only for forward scenario dates (currently: 2031-03-31). **Any freshness/"Data As Of" logic must exclude rows where this is TRUE — see `fact_source_refresh`.** |
| observation_type | VARCHAR(30) | 'Year-End Reported' / 'In-Year Management Disclosure' / 'Event-Driven' / 'Scenario Horizon' |
| source_dataset_id | VARCHAR(10) | FK-by-convention to data_source_register.csv |

## dim_municipality
| Column | Type | Notes |
|---|---|---|
| municipality_key | INTEGER PK | 0 = group-total placeholder |
| municipality_name | VARCHAR(100) | |
| municipality_type | VARCHAR(20) | Metro/Local/District/Group-Total |
| province_key | INTEGER FK | NULL for group-total |
| is_group_total_placeholder | BOOLEAN | Distinguishes the aggregate row from a real municipality |
| source_dataset_id | VARCHAR(10) | |

## dim_debt_status
| Column | Type | Notes |
|---|---|---|
| debt_status_key | INTEGER PK | |
| debt_status_name | VARCHAR(50) | e.g. 'Aggregate Exposure (mixed underlying status)', 'Delinquent', 'Settled' |
| applies_to_grain | VARCHAR(20) | 'Group-Total' or 'Individual Municipality' — enforces that a group-total row is never labelled with a single-entity operational status |

## dim_customer_segment
Standard segment reference. `is_aggregate` flags the ALL-SEGMENTS rollup row (segment_key=0).

## dim_incident_type
Controlled vocabulary of Eskom's named physical-security crime categories. `incident_type_key = 0`
is the reserved aggregate key used for Eskom's FY2026 disclosure, which does not break down by
category — see the mandatory scope note in `docs/data_model.md`.

## dim_legal_status
Controlled vocabulary for case legal-process stages (Allegation → Investigation → Arrest → Charge
→ Conviction → Sentence → Case Closed). `sequence_order` documents typical progression but a case
may skip stages.

## dim_metric
Distinct security KPI metrics (Incident Count YoY, Estimated Loss, Arrests, Recoveries,
Convictions, and their YoY% counterparts), each independently addressable for source lineage.

## dim_location / dim_province
Standard reference dimensions.

## fact_municipal_debt
Grain: one row per (date_key, municipality_key). Holds **actuals only** — no scenario rows (see
`fact_municipal_debt_scenario`).
| Column | Type | Notes |
|---|---|---|
| gross_arrears_rand | NUMERIC(18,2) | CHECK >= 0 |
| write_off_rand | NUMERIC(18,2) | Nullable |
| debt_status_key | INTEGER FK | |
| evidence_type | VARCHAR(30) | 'FACT_REPORTED' or 'CALCULATION_DERIVED' — never blank |
| calculation_method | VARCHAR(200) | Populated only when evidence_type = 'CALCULATION_DERIVED' |
| source_dataset_id | VARCHAR(10) | NOT NULL |

**Point-in-time warning:** this table legitimately holds multiple rows for the same
`municipality_key = 0` group total (different `date_key` values). Never `SUM(gross_arrears_rand)`
across the whole table for a "current balance" — see `powerbi/dax/measures.dax`
`Latest Reported Municipal Debt` for the correct pattern, and
`docs/technical_audit.md` P0-3 for the bug this replaced.

## fact_municipal_debt_relief_programme
Grain: one row per programme. Holds the National Treasury-approved legacy-debt amount and approved
municipality count. The R55.3bn value is intentionally absent from `fact_municipal_debt`.

## fact_corporate_metric
Grain: one row per (date_key, metric_name). Holds EAF and net-profit observations with domain,
unit, evidence type and source lineage.

## fact_municipal_debt_scenario
Grain: one row per (date_key, scenario_name). **Physically separate table** from
`fact_municipal_debt` — no shared primary key, so a naive join/union cannot blend scenario and
actual observations. `evidence_type` is always a SCENARIO_* value.

## fact_electricity_sales
Grain: one row per (date_key, segment_key). Only segment_key=0 (ALL SEGMENTS) populated — Data Gap #2.

## fact_security_metric
Grain: one row per (reporting_date_key, incident_type_key, metric_key, location_key). Each row
is one disclosed number with its own `source_dataset_id` — replaces the Phase-1
`fact_security_incidents` table, which bundled five metrics from one disclosure event onto a
single row under one shared source ID.

## fact_security_case
Grain: one row per individually-named, individually-sourced security case. `source_dataset_id`
must resolve to the specific article/release describing *that case* — never a general
organisational article (see `docs/technical_audit.md` P0-2).

## fact_security_case_event
Grain: one row per chronological legal-process event within a case (many events per case
possible). `legal_status_key` is always a single atomic value from `dim_legal_status` — composite
strings like "Mixed (Arrest+Conviction...)" are prohibited by design.

## fact_source_refresh
Grain: one row per dataset_id. Drives "Data reported as of" / "Data last refreshed" labels.
Structurally excludes SCENARIO_* evidence-type datasets at load time (see
`sql/13_source_freshness.sql`) so scenario dates can never surface as a freshness label.

## fact_tariff_adjustment
Grain: one row per (effective_date_key, customer_group). Holds implemented average tariffs and a
separately qualified forward average price path.

| Column | Type | Notes |
|---|---|---|
| effective_date_key | INTEGER FK | Intended or implemented effective date in `dim_date` |
| fiscal_year_label | VARCHAR(10) | Regulatory financial-year label |
| customer_group | VARCHAR(60) | Direct, municipal bulk or average price path |
| increase_pct | NUMERIC(6,2) | Published average percentage increase; not a bill forecast |
| intended_effective_date | DATE | Effective/intended date for the observation |
| regulatory_status | VARCHAR(240) | Preserves implementation/consultation status |
| evidence_type | VARCHAR(30) | `FACT_REPORTED` for the published regulatory observation |
| source_dataset_id | VARCHAR(10) | Lineage for the numeric value |
| status_source_dataset_id | VARCHAR(10) | Separate lineage for current regulatory status |

## Power BI semantic export views

`vw_powerbi_period`, `vw_powerbi_metric`, `vw_powerbi_tariff`, `vw_powerbi_scenario` and
`vw_powerbi_source` form the only supported SQLite-to-Power-BI interface. Their columns map exactly
to the six generated TMDL tables. The PBIP generator does not contain a parallel fact dataset.
