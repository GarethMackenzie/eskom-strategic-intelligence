-- ============================================================================
-- 12_executive_kpis.sql
-- Rebuilt to resolve the "latest reported observation" for each KPI
-- explicitly, rather than hand-typing static values as in Phase 1 (which
-- worked but didn't demonstrate that the resolution logic is correct and
-- reusable). Scenario KPIs pulled from fact_municipal_debt_scenario
-- separately and clearly labelled -- no shared query with the actuals.
-- ============================================================================

DROP VIEW IF EXISTS vw_executive_kpis_actual;
CREATE VIEW vw_executive_kpis_actual AS
WITH latest_group_debt AS (
    SELECT gross_arrears_rand, evidence_type, source_dataset_id,
           ROW_NUMBER() OVER (ORDER BY date_key DESC) AS rn
    FROM fact_municipal_debt WHERE municipality_key = 0
),
prior_group_debt AS (
    SELECT gross_arrears_rand,
           ROW_NUMBER() OVER (ORDER BY date_key DESC) AS rn
    FROM fact_municipal_debt f JOIN dim_date d ON f.date_key = d.date_key
    WHERE municipality_key = 0 AND d.is_fiscal_year_end = TRUE
),
latest_sales AS (
    SELECT sales_twh, revenue_rand, ROW_NUMBER() OVER (ORDER BY date_key DESC) AS rn
    FROM fact_electricity_sales WHERE segment_key = 0
)
SELECT 'Municipal arrears (latest reported)' AS kpi_name,
       CAST(gross_arrears_rand / 1000000000 AS VARCHAR) AS kpi_value, 'R billion' AS kpi_unit,
       source_dataset_id, evidence_type
FROM latest_group_debt WHERE rn = 1
UNION ALL
SELECT 'Electricity sales volume (latest reported)', CAST(sales_twh AS VARCHAR), 'TWh', 'DS006', 'FACT_REPORTED'
FROM latest_sales WHERE rn = 1;

-- Scenario KPI -- separate view, never unioned with the actuals view above,
-- so a careless SELECT * cannot blend them (fixes P0-5 at the query layer
-- as well as the storage layer).
DROP VIEW IF EXISTS vw_executive_kpis_scenario;
CREATE VIEW vw_executive_kpis_scenario AS
SELECT 'SCENARIO -- NOT MANAGEMENT FORECAST' AS display_label,
       scenario_name, projected_arrears_rand / 1000000000 AS projected_arrears_r_billion,
       source_dataset_id
FROM fact_municipal_debt_scenario;

SELECT * FROM vw_executive_kpis_actual;
SELECT * FROM vw_executive_kpis_scenario;
