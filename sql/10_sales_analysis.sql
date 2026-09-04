-- ============================================================================
-- 10_sales_analysis.sql
-- fact_electricity_sales schema was not flagged in the technical audit as
-- defective (Data Gap #2 remains open -- segment-level data still not
-- sourced -- see docs/limitations.md); logic re-verified against the audit's
-- findings and is otherwise unchanged from Phase 1.
-- ============================================================================

WITH annual_sales AS (
    SELECT
        d.fiscal_year_label,
        s.segment_key,
        seg.segment_name,
        s.sales_twh,
        s.revenue_rand,
        LAG(s.sales_twh) OVER (PARTITION BY s.segment_key ORDER BY d.fiscal_year) AS prior_year_twh
    FROM fact_electricity_sales s
    JOIN dim_date d ON s.date_key = d.date_key
    JOIN dim_customer_segment seg ON s.segment_key = seg.segment_key
    WHERE d.is_fiscal_year_end = TRUE
)
SELECT
    fiscal_year_label,
    segment_name,
    sales_twh,
    prior_year_twh,
    ROUND(100.0 * (sales_twh - prior_year_twh) / NULLIF(prior_year_twh, 0), 2) AS yoy_pct,
    revenue_rand,
    CASE WHEN revenue_rand IS NOT NULL AND sales_twh IS NOT NULL
         THEN ROUND(revenue_rand / (sales_twh * 1000000000), 4)
         ELSE NULL END AS implied_rand_per_kwh
FROM annual_sales
ORDER BY segment_name, fiscal_year_label;

-- ----------------------------------------------------------------------------
-- Structural-contradiction query: sales volume vs. plant availability (EAF).
-- Still a diagnostic (not causal) join across two independently sourced
-- series. EAF remains an illustrative CTE with literal cited values (DS012)
-- pending a dedicated fact table -- unchanged limitation from Phase 1,
-- re-confirmed as still accurate in this pass.
-- ----------------------------------------------------------------------------
WITH sales AS (
    SELECT d.fiscal_year_label, s.sales_twh
    FROM fact_electricity_sales s JOIN dim_date d ON s.date_key = d.date_key
    WHERE s.segment_key = 0 AND d.is_fiscal_year_end = TRUE
),
eaf AS (
    SELECT 'FY2025' AS fiscal_year_label, 60.6 AS energy_availability_factor_pct
    UNION ALL
    SELECT 'FY2026', 65.16
)
SELECT s.fiscal_year_label, s.sales_twh, e.energy_availability_factor_pct,
       'Sales volume declined in the same period plant availability improved. This is a diagnostic observation, not a causal finding -- see report Section: Demand Analytics.' AS interpretive_note
FROM sales s JOIN eaf e ON s.fiscal_year_label = e.fiscal_year_label
ORDER BY s.fiscal_year_label;
