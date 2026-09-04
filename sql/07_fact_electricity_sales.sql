-- ============================================================================
-- 07_fact_electricity_sales.sql
-- Grain: one row per (date_key, segment_key). Only ALL SEGMENTS (segment_key=0)
-- populated in Phase 1 -- see Data Gap #2.
-- ============================================================================

DROP TABLE IF EXISTS fact_electricity_sales;
CREATE TABLE fact_electricity_sales (
    date_key            INTEGER REFERENCES dim_date(date_key),
    segment_key          INTEGER REFERENCES dim_customer_segment(segment_key),
    sales_twh              NUMERIC(10,2),
    revenue_rand             NUMERIC(18,2),
    source_dataset_id        VARCHAR(10),
    PRIMARY KEY (date_key, segment_key)
);

INSERT INTO fact_electricity_sales (date_key, segment_key, sales_twh, revenue_rand, source_dataset_id) VALUES
(20250331, 0, 189.70, NULL, 'DS006'),
(20260331, 0, 178.00, 354700000000.00, 'DS006');
-- FY2025 revenue intentionally left NULL: DS007 discloses FY2026 revenue and its
-- +4.1% YoY growth rate, from which FY2025 revenue *could* be back-solved
-- (354.7bn / 1.041 ≈ R340.7bn), but that back-solve is not yet verified against
-- an independently reported FY2025 revenue figure, so it is left as a documented
-- CALCULATION opportunity rather than inserted as if it were a FACT.
