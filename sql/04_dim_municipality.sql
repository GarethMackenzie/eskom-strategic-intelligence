-- ============================================================================
-- 04_dim_municipality.sql
-- See docs/data_model.md "Data Gap #1": a full municipality list is not yet
-- sourced. This table is intentionally sparse and includes a group-total
-- placeholder key so that group-level facts (the only ones currently
-- available) have somewhere valid to join.
-- ============================================================================

DROP TABLE IF EXISTS dim_province;
CREATE TABLE dim_province (
    province_key    INTEGER PRIMARY KEY,
    province_name   VARCHAR(50) NOT NULL
);

INSERT INTO dim_province (province_key, province_name) VALUES
(1, 'Eastern Cape'), (2, 'Free State'), (3, 'Gauteng'), (4, 'KwaZulu-Natal'),
(5, 'Limpopo'), (6, 'Mpumalanga'), (7, 'Northern Cape'), (8, 'North West'),
(9, 'Western Cape');

DROP TABLE IF EXISTS dim_municipality;
CREATE TABLE dim_municipality (
    municipality_key    INTEGER PRIMARY KEY,
    municipality_name   VARCHAR(100) NOT NULL,
    municipality_type    VARCHAR(20),            -- Metro / Local / District / Group-Total
    province_key          INTEGER REFERENCES dim_province(province_key),
    is_group_total_placeholder BOOLEAN NOT NULL DEFAULT FALSE,
    source_dataset_id     VARCHAR(10)
);

-- Group-total placeholder: the only key that carries the R111.6bn / R119.9bn
-- Eskom-wide figures until Data Gap #1 is closed with a real municipal table.
INSERT INTO dim_municipality (municipality_key, municipality_name, municipality_type, province_key, is_group_total_placeholder, source_dataset_id) VALUES
(0, 'ALL MUNICIPALITIES (Eskom-wide total)', 'Group-Total', NULL, TRUE, 'DS001');

-- The single individually-verified, dated, sourced municipality-level record.
INSERT INTO dim_municipality (municipality_key, municipality_name, municipality_type, province_key, is_group_total_placeholder, source_dataset_id) VALUES
(1, 'City of Johannesburg / City Power', 'Metro', 3, FALSE, 'DS020');

-- DO NOT add further municipality rows with invented balances. When Data Gap #1
-- is closed, extend this INSERT block with real, sourced rows and update
-- docs/data_source_register.csv and docs/limitations.md accordingly.
