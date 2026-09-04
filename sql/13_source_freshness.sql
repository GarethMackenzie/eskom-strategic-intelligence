-- ============================================================================
-- 13_source_freshness.sql
-- Fixes P0-4 (docs/technical_audit.md): "Data As Of" must never be able to
-- resolve to a scenario date. Rather than relying on every future DAX
-- measure/query to remember to filter dim_date on is_scenario_horizon=FALSE,
-- this table is the single authoritative source for freshness labels, and it
-- is seeded ONLY from actual dataset retrieval events -- scenario dataset IDs
-- (including DS003 and DS024B) are structurally excluded by
-- population, not by a filter that could be forgotten.
-- ============================================================================

DROP TABLE IF EXISTS fact_source_refresh;
CREATE TABLE fact_source_refresh (
    dataset_id             VARCHAR(10) PRIMARY KEY REFERENCES stg_data_source_register(dataset_id),
    source_reporting_date    DATE NOT NULL,     -- publication_date from the register
    retrieved_at                 TIMESTAMP NOT NULL,
    last_verified_at                TIMESTAMP NOT NULL,
    refresh_status                     VARCHAR(20) NOT NULL DEFAULT 'Current'  -- Current / Stale / Superseded
);

-- The build pipeline loads docs/data_source_register.csv into staging first.
-- Scenario statements are structurally excluded from report freshness.
INSERT INTO fact_source_refresh (
    dataset_id, source_reporting_date, retrieved_at, last_verified_at, refresh_status
)
SELECT
    dataset_id,
    date(publication_date),
    datetime(retrieval_datetime),
    datetime(last_verified_datetime),
    CASE
        WHEN LOWER(verification_status) LIKE '%superseded%' THEN 'Superseded'
        ELSE 'Current'
    END
FROM stg_data_source_register
WHERE evidence_type NOT LIKE 'SCENARIO%'
  AND LOWER(verification_status) NOT LIKE '%superseded%';

-- The single "Data Reported As Of" value for the whole report is the MAX
-- source_reporting_date across this table -- i.e. the most recent primary
-- disclosure event actually used, never a scenario horizon.
DROP VIEW IF EXISTS vw_report_freshness;
CREATE VIEW vw_report_freshness AS
SELECT
    MAX(source_reporting_date) AS data_reported_as_of,
    MAX(retrieved_at) AS pipeline_last_refreshed
FROM fact_source_refresh;
