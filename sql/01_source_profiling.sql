-- ============================================================================
-- 01_source_profiling.sql
-- Profiles docs/data_source_register.csv (loaded as staging table
-- stg_data_source_register) to surface coverage gaps before any modelling.
-- ============================================================================

-- Assumes stg_data_source_register mirrors data_source_register.csv columns.

-- Coverage by data-quality rating
SELECT data_quality_rating, COUNT(*) AS n_sources
FROM stg_data_source_register
GROUP BY data_quality_rating
ORDER BY n_sources DESC;

-- Coverage by publisher (are we over-reliant on secondary press vs primary Eskom disclosure?)
SELECT source_publisher, COUNT(*) AS n_sources
FROM stg_data_source_register
GROUP BY source_publisher
ORDER BY n_sources DESC;

-- Staleness check: sources older than 12 months from retrieval_date at query time
SELECT dataset_id, metric, publication_date, retrieval_datetime
FROM stg_data_source_register
WHERE julianday(substr(retrieval_datetime, 1, 10)) - julianday(publication_date) > 365;

-- Sources still marked as requiring Phase 2 follow-up (by convention, notes
-- containing 'Data Gap' or 'Phase 2')
SELECT dataset_id, metric, notes
FROM stg_data_source_register
WHERE LOWER(notes) LIKE '%data gap%' OR LOWER(notes) LIKE '%phase 2%';
