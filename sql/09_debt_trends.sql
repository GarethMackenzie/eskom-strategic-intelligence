-- ============================================================================
-- 09_debt_trends.sql
-- Rebuilt against the corrected schema: fact_municipal_debt no longer
-- contains scenario rows (see fact_municipal_debt_scenario), and status is
-- now debt_status_key with aggregate-vs-individual semantics.
-- ============================================================================

-- CTE 1: group-total, fiscal-year-end only, ACTUAL rows (evidence_type is
-- either FACT_REPORTED or CALCULATION_DERIVED -- both are actuals; scenario
-- rows cannot appear here at all because they physically live in a
-- different table).
WITH group_total_year_end AS (
    SELECT
        d.fiscal_year,
        d.fiscal_year_label,
        f.gross_arrears_rand,
        f.write_off_rand,
        f.evidence_type,
        f.source_dataset_id
    FROM fact_municipal_debt f
    JOIN dim_date d ON f.date_key = d.date_key
    WHERE f.municipality_key = 0
      AND d.is_fiscal_year_end = TRUE
),

yoy AS (
    SELECT
        fiscal_year_label,
        gross_arrears_rand,
        evidence_type,
        LAG(gross_arrears_rand) OVER (ORDER BY fiscal_year) AS prior_year_arrears,
        gross_arrears_rand - LAG(gross_arrears_rand) OVER (ORDER BY fiscal_year) AS yoy_change_rand,
        ROUND(
            100.0 * (gross_arrears_rand - LAG(gross_arrears_rand) OVER (ORDER BY fiscal_year))
            / NULLIF(LAG(gross_arrears_rand) OVER (ORDER BY fiscal_year), 0)
        , 2) AS yoy_growth_pct,
        COUNT(*) OVER () AS n_years_available
    FROM group_total_year_end
)

SELECT
    fiscal_year_label,
    gross_arrears_rand,
    evidence_type,
    prior_year_arrears,
    yoy_change_rand,
    yoy_growth_pct,
    CASE
        WHEN n_years_available < 5 THEN
            'CAGR not calculated: fewer than 5 comparable annual points available (n=' || n_years_available || '). See docs/limitations.md Data Gap #4.'
        ELSE 'CAGR calculable -- see rolling window below'
    END AS cagr_data_sufficiency_flag
FROM yoy
ORDER BY fiscal_year_label;

-- ----------------------------------------------------------------------------
-- Debt-growth waterfall components (unchanged in intent from Phase 1, updated
-- for renamed columns).
-- ----------------------------------------------------------------------------
SELECT
    d.fiscal_year_label,
    f.gross_arrears_rand AS closing_balance,
    f.write_off_rand,
    f.gross_arrears_rand + COALESCE(f.write_off_rand, 0) AS implied_pre_writeoff_balance,
    f.evidence_type,
    f.source_dataset_id
FROM fact_municipal_debt f
JOIN dim_date d ON f.date_key = d.date_key
WHERE f.municipality_key = 0 AND d.is_fiscal_year_end = TRUE
ORDER BY d.fiscal_year_label;

-- ----------------------------------------------------------------------------
-- City of Johannesburg latest-status query (unchanged pattern from Phase 1;
-- validated to still correctly resolve to 'Settled' as of any as_of date on
-- or after 2026-08-21).
-- ----------------------------------------------------------------------------
WITH ranked_status AS (
    SELECT
        m.municipality_name,
        d.calendar_date,
        ds.debt_status_name,
        f.gross_arrears_rand,
        ROW_NUMBER() OVER (
            PARTITION BY f.municipality_key
            ORDER BY d.calendar_date DESC
        ) AS recency_rank
    FROM fact_municipal_debt f
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_municipality m ON f.municipality_key = m.municipality_key
    JOIN dim_debt_status ds ON f.debt_status_key = ds.debt_status_key
    WHERE f.municipality_key = 1
      AND d.calendar_date <= CURRENT_DATE
)
SELECT municipality_name, calendar_date AS as_of_date, debt_status_name, gross_arrears_rand
FROM ranked_status
WHERE recency_rank = 1;

-- ----------------------------------------------------------------------------
-- Scenario query -- deliberately separate from every query above. Anyone
-- reading this file top to bottom sees the physical boundary: everything
-- above this line is ACTUAL data; only this final block touches the
-- scenario table, and it is clearly labelled as such in its own SELECT.
-- ----------------------------------------------------------------------------
SELECT
    'SCENARIO -- NOT A MANAGEMENT FORECAST' AS display_label,
    scenario_name,
    projected_arrears_rand,
    assumptions,
    source_dataset_id
FROM fact_municipal_debt_scenario;
