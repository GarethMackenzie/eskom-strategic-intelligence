-- ============================================================================
-- 02_data_quality.sql
-- Data-quality framework per project brief: duplicates, null keys, impossible
-- dates, negative values where inappropriate, inconsistent reporting periods,
-- unit-conversion sanity, duplicate incidents.
-- Run after loading all dim/fact tables. Every check should return 0 rows.
-- ============================================================================

-- 1. Duplicate primary keys in fact_municipal_debt
SELECT date_key, municipality_key, COUNT(*) AS dup_count
FROM fact_municipal_debt
GROUP BY date_key, municipality_key
HAVING COUNT(*) > 1;

-- 2. Null foreign keys (orphaned facts)
SELECT f.*
FROM fact_municipal_debt f
LEFT JOIN dim_date d ON f.date_key = d.date_key
LEFT JOIN dim_municipality m ON f.municipality_key = m.municipality_key
WHERE d.date_key IS NULL OR m.municipality_key IS NULL;

-- 3. Impossible / future-dated FACT rows (scenario horizons are excluded via
--    the date dimension; the actuals fact must not contain scenario evidence)
SELECT f.*
FROM fact_municipal_debt f
JOIN dim_date d ON f.date_key = d.date_key
WHERE d.is_scenario_horizon = FALSE
  AND date(f.date_key / 10000 || '-' || printf('%02d', (f.date_key / 100) % 100) || '-' || printf('%02d', f.date_key % 100)) > date('now');

-- 4. Negative arrears values (inappropriate for a debt-owed measure; R0 is
--    valid -- e.g. City Power post-settlement -- negative is not)
SELECT * FROM fact_municipal_debt WHERE gross_arrears_rand < 0;

-- 5. Sales volume unit sanity check: TWh values should be in a plausible
--    national-utility range (10 - 500 TWh); catches accidental MWh/kWh entry
SELECT * FROM fact_electricity_sales WHERE sales_twh NOT BETWEEN 10 AND 500;

-- 6. Reporting-period consistency: flag any fact row whose date_key's fiscal
--    year does not match the fiscal_year stored on dim_date (guards against
--    manual seeding errors as the table grows)
SELECT f.*, d.fiscal_year_label
FROM fact_electricity_sales f
JOIN dim_date d ON f.date_key = d.date_key
WHERE d.fiscal_year != CAST(SUBSTRING(CAST(d.date_key AS VARCHAR), 1, 4) AS INTEGER)
  AND d.is_fiscal_year_end = TRUE;

-- 7. Duplicate named security cases (same location + opened date + summary)
SELECT location_key, opened_date, case_summary, COUNT(*)
FROM fact_security_case
GROUP BY location_key, opened_date, case_summary
HAVING COUNT(*) > 1;

-- 8. Scenario evidence must never re-enter the actuals fact.
SELECT * FROM fact_municipal_debt
WHERE evidence_type LIKE 'SCENARIO%';

-- 9. Every legal-process event must use a controlled status key.
SELECT e.*
FROM fact_security_case_event e
LEFT JOIN dim_legal_status s ON e.legal_status_key = s.legal_status_key
WHERE s.legal_status_key IS NULL;

-- 10. Canonical annual debt series must span FY2015-FY2026 with 12 rows.
SELECT 'invalid annual debt series shape' AS violation
WHERE (
    SELECT COUNT(*)
    FROM fact_municipal_debt f JOIN dim_date d USING (date_key)
    WHERE f.municipality_key = 0 AND d.is_fiscal_year_end = TRUE
) <> 12;

-- 11. FY2024 total arrears is R74.4bn; R55.3bn must not appear in total actuals.
SELECT * FROM fact_municipal_debt
WHERE municipality_key = 0
  AND ((date_key = 20240331 AND gross_arrears_rand <> 74400000000)
       OR gross_arrears_rand = 55300000000);

-- 12. The R55.3bn programme scope must remain in its dedicated table.
SELECT * FROM fact_municipal_debt_relief_programme
WHERE approved_legacy_debt_rand <> 55300000000
   OR approved_municipalities <> 71;

-- 13. Every Power BI metric observation must resolve to a governed source.
SELECT p.*
FROM vw_powerbi_metric p
LEFT JOIN stg_data_source_register s ON p.SourceDatasetId = s.dataset_id
WHERE s.dataset_id IS NULL;

-- 14. Tariff rows require separate numeric-value and regulatory-status lineage.
SELECT * FROM fact_tariff_adjustment
WHERE source_dataset_id IS NULL OR status_source_dataset_id IS NULL;
