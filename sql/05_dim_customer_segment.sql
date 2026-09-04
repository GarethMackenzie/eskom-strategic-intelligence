-- ============================================================================
-- 05_dim_customer_segment.sql
-- See docs/data_model.md / Data Gap #2: segment-level TWh splits are not yet
-- sourced at primary-source detail. Dimension is fully defined (so the model
-- and DAX/Power Query can be built against a stable schema); only the
-- 'ALL_SEGMENTS' aggregate row currently has populated fact data.
-- ============================================================================

DROP TABLE IF EXISTS dim_customer_segment;
CREATE TABLE dim_customer_segment (
    segment_key         INTEGER PRIMARY KEY,
    segment_name        VARCHAR(50) NOT NULL,
    is_aggregate        BOOLEAN NOT NULL DEFAULT FALSE
);

INSERT INTO dim_customer_segment (segment_key, segment_name, is_aggregate) VALUES
(0, 'ALL SEGMENTS (Eskom-wide total)', TRUE),
(1, 'Municipalities / Distributors', FALSE),
(2, 'Industrial', FALSE),
(3, 'Mining', FALSE),
(4, 'Commercial', FALSE),
(5, 'Residential (direct)', FALSE),
(6, 'Agriculture', FALSE),
(7, 'Rail', FALSE),
(8, 'International (SAPP exports)', FALSE);
