-- Tariff and revenue-path observations. The FY2027/28 row deliberately
-- distinguishes the approved average path from the retail tariff structure,
-- which was still under NERSA consultation on 4 September 2026.

DROP TABLE IF EXISTS fact_tariff_adjustment;
CREATE TABLE fact_tariff_adjustment (
    effective_date_key       INTEGER NOT NULL REFERENCES dim_date(date_key),
    fiscal_year_label        VARCHAR(10) NOT NULL,
    customer_group           VARCHAR(60) NOT NULL,
    increase_pct             NUMERIC(6,2) NOT NULL CHECK (increase_pct > 0 AND increase_pct < 100),
    intended_effective_date  DATE NOT NULL,
    regulatory_status        VARCHAR(240) NOT NULL,
    evidence_type            VARCHAR(30) NOT NULL DEFAULT 'FACT_REPORTED',
    source_dataset_id        VARCHAR(10) NOT NULL,
    status_source_dataset_id VARCHAR(10) NOT NULL,
    PRIMARY KEY (effective_date_key, customer_group)
);

INSERT INTO fact_tariff_adjustment VALUES
(20250401, 'FY2025/26', 'Direct customers - average', 12.74, '2025-04-01',
 'Approved and implemented', 'FACT_REPORTED', 'DS035', 'DS035'),
(20260401, 'FY2026/27', 'Direct customers - average', 8.76, '2026-04-01',
 'Approved and implemented', 'FACT_REPORTED', 'DS036', 'DS036'),
(20260701, 'FY2026/27', 'Municipal bulk purchases', 9.01, '2026-07-01',
 'Approved and implemented', 'FACT_REPORTED', 'DS036', 'DS036'),
(20270401, 'FY2027/28', 'Average price path', 8.83, '2027-04-01',
 'Average revenue/price path established; detailed retail tariff structure and customer-category allocation under NERSA consultation as at 2026-09-04',
 'FACT_REPORTED', 'DS035', 'DS037');

DROP VIEW IF EXISTS vw_tariff_path;
CREATE VIEW vw_tariff_path AS
SELECT
    fiscal_year_label,
    customer_group,
    increase_pct,
    intended_effective_date,
    regulatory_status,
    source_dataset_id,
    status_source_dataset_id
FROM fact_tariff_adjustment
ORDER BY effective_date_key, customer_group;
