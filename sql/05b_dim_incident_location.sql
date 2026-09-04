-- ============================================================================
-- 05b_dim_incident_location.sql
-- See docs/data_model.md: Eskom's FY2026 disclosed security KPIs are AGGREGATE
-- across all crime categories. This dimension is defined per the brief's
-- taxonomy, but FactSecurityIncident (07_fact tables below) only populates the
-- 'aggregate_all_categories' key for the FY2026 KPI row.
-- ============================================================================

DROP TABLE IF EXISTS dim_incident_type;
CREATE TABLE dim_incident_type (
    incident_type_key    INTEGER PRIMARY KEY,
    incident_type_name   VARCHAR(60) NOT NULL,
    category_group       VARCHAR(30)             -- 'Coal/Fuel', 'Infrastructure', 'Revenue/Fraud'
);

INSERT INTO dim_incident_type (incident_type_key, incident_type_name, category_group) VALUES
(0, 'AGGREGATE - ALL CATEGORIES (Eskom FY2026 disclosure)', 'Aggregate'),
(1, 'Cable theft', 'Infrastructure'),
(2, 'Coal theft', 'Coal/Fuel'),
(3, 'Coal diversion / adulteration / quality manipulation', 'Coal/Fuel'),
(4, 'Diesel / fuel-oil theft', 'Coal/Fuel'),
(5, 'Illegal connections', 'Revenue/Fraud'),
(6, 'Meter tampering', 'Revenue/Fraud'),
(7, 'Ghost vending', 'Revenue/Fraud'),
(8, 'Infrastructure vandalism', 'Infrastructure'),
(9, 'Sabotage', 'Infrastructure'),
(10, 'Procurement fraud', 'Revenue/Fraud'),
(11, 'Equipment/component theft (non-cable, non-coal, non-fuel)', 'Infrastructure');

DROP TABLE IF EXISTS dim_location;
CREATE TABLE dim_location (
    location_key       INTEGER PRIMARY KEY,
    location_name       VARCHAR(80) NOT NULL,
    location_type        VARCHAR(20),             -- 'Power Station', 'Corporate', 'National'
    province_key          INTEGER REFERENCES dim_province(province_key)
);

INSERT INTO dim_location (location_key, location_name, location_type, province_key) VALUES
(0, 'NATIONAL (all sites)', 'National', NULL),
(1, 'Camden Power Station', 'Power Station', 6),
(2, 'Matla Power Station', 'Power Station', 6),
(3, 'Kendal Power Station', 'Power Station', 6),
(4, 'Tutuka Power Station', 'Power Station', 6),
(5, 'Matimba Power Station', 'Power Station', 5),
(6, 'Port Rex Power Station', 'Power Station', 1),
(7, 'Arnot Power Station', 'Power Station', 6);
