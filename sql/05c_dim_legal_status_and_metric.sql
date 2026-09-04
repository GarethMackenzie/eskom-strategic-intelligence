-- ============================================================================
-- 05c_dim_legal_status_and_metric.sql
-- Fixes P1-2 from docs/technical_audit.md: legal status must be an atomic,
-- controlled value, never a composite string like
-- 'Mixed (Arrest+Conviction, aggregated across cases)'.
-- ============================================================================

DROP TABLE IF EXISTS dim_legal_status;
CREATE TABLE dim_legal_status (
    legal_status_key    INTEGER PRIMARY KEY,
    legal_status_name   VARCHAR(30) NOT NULL,
    sequence_order       INTEGER NOT NULL      -- typical chronological order; a case can skip
                                                -- steps (e.g. straight to Case Closed) but never
                                                -- regress without an explicit new event
);

INSERT INTO dim_legal_status (legal_status_key, legal_status_name, sequence_order) VALUES
(1, 'Allegation', 1),
(2, 'Investigation', 2),
(3, 'Arrest', 3),
(4, 'Charge', 4),
(5, 'Conviction', 5),
(6, 'Sentence', 6),
(7, 'Case Closed - No Charge', 7),
(8, 'Case Closed - Withdrawn', 7);

-- ----------------------------------------------------------------------------
-- dim_metric: for fact_security_metric (Step 4 remediation). Distinct KPI
-- metrics that Eskom discloses, so each observation can carry its own
-- source_dataset_id rather than five metrics sharing one row/one source.
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS dim_metric;
CREATE TABLE dim_metric (
    metric_key     INTEGER PRIMARY KEY,
    metric_name    VARCHAR(40) NOT NULL,
    unit             VARCHAR(20) NOT NULL
);

INSERT INTO dim_metric (metric_key, metric_name, unit) VALUES
(1, 'Incident Count YoY Change', 'Percent'),
(2, 'Estimated Financial Loss', 'Rand'),
(3, 'Arrests', 'Count'),
(4, 'Recoveries', 'Rand'),
(5, 'Convictions', 'Count'),
(6, 'Estimated Financial Loss YoY Change', 'Percent'),
(7, 'Recoveries YoY Change', 'Percent'),
(8, 'Arrests YoY Change', 'Percent');
