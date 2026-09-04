-- ============================================================================
-- 11_pareto_analysis.sql
-- Updated for the corrected schema (debt_status_key, evidence_type). Still
-- returns zero rows by design until Data Gap #1 (municipality-level arrears
-- table) closes -- re-confirmed in this pass's research (Step 12): no
-- primary municipality-by-municipality debtor schedule was located.
-- ============================================================================

WITH latest_balance_per_municipality AS (
    SELECT
        m.municipality_key,
        m.municipality_name,
        f.gross_arrears_rand,
        ds.debt_status_name,
        ROW_NUMBER() OVER (PARTITION BY f.municipality_key ORDER BY f.date_key DESC) AS rn
    FROM fact_municipal_debt f
    JOIN dim_municipality m ON f.municipality_key = m.municipality_key
    JOIN dim_debt_status ds ON f.debt_status_key = ds.debt_status_key
    WHERE m.is_group_total_placeholder = FALSE
),
current_balances AS (
    SELECT municipality_key, municipality_name, gross_arrears_rand
    FROM latest_balance_per_municipality
    WHERE rn = 1 AND gross_arrears_rand > 0
),
ranked AS (
    SELECT
        municipality_name,
        gross_arrears_rand,
        RANK() OVER (ORDER BY gross_arrears_rand DESC) AS debt_rank,
        ROUND(100.0 * gross_arrears_rand / SUM(gross_arrears_rand) OVER (), 2) AS pct_of_named_total,
        ROUND(100.0 * SUM(gross_arrears_rand) OVER (ORDER BY gross_arrears_rand DESC)
              / SUM(gross_arrears_rand) OVER (), 2) AS cumulative_pct
    FROM current_balances
)
SELECT * FROM ranked ORDER BY debt_rank;

-- Expected result: ZERO rows. The only individually-disclosed municipality,
-- City of Johannesburg, is currently Settled (R0) and therefore correctly
-- excluded from a delinquency ranking. This is not a bug -- see
-- docs/limitations.md Data Gap #1, re-confirmed still open in this pass.
