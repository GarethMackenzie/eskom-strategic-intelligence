-- Canonical, validated export layer consumed by the Power BI generator.
-- The PBIP builder reads these views from SQLite after release-blocking QA;
-- no business facts are duplicated in Python.

DROP TABLE IF EXISTS fact_corporate_metric;
CREATE TABLE fact_corporate_metric (
    date_key          INTEGER NOT NULL REFERENCES dim_date(date_key),
    domain            VARCHAR(40) NOT NULL,
    metric_name       VARCHAR(80) NOT NULL,
    metric_value      NUMERIC(18,4) NOT NULL,
    unit              VARCHAR(20) NOT NULL,
    evidence_type     VARCHAR(30) NOT NULL DEFAULT 'FACT_REPORTED',
    source_dataset_id VARCHAR(10) NOT NULL,
    PRIMARY KEY (date_key, metric_name)
);

INSERT INTO fact_corporate_metric VALUES
(20250331, 'Operations', 'Energy Availability Factor', 60.6, 'Percent', 'FACT_REPORTED', 'DS012'),
(20260331, 'Operations', 'Energy Availability Factor', 65.16, 'Percent', 'FACT_REPORTED', 'DS012'),
(20260331, 'Financial', 'Net Profit After Tax', 30300000000, 'Rand', 'FACT_REPORTED', 'DS009');

DROP VIEW IF EXISTS vw_powerbi_period;
CREATE VIEW vw_powerbi_period AS
SELECT
    date_key AS PeriodKey,
    fiscal_year_label AS FiscalYear,
    calendar_date AS EffectiveDate,
    CASE
        WHEN is_scenario_horizon THEN fiscal_year_label || ' scenario'
        WHEN is_fiscal_year_end THEN fiscal_year_label || ' year-end'
        ELSE observation_type
    END AS PeriodLabel,
    ROW_NUMBER() OVER (ORDER BY calendar_date, date_key) AS SortOrder,
    is_fiscal_year_end AS IsFiscalYearEnd,
    is_scenario_horizon AS IsScenarioHorizon
FROM dim_date;

DROP VIEW IF EXISTS vw_powerbi_metric;
CREATE VIEW vw_powerbi_metric AS
SELECT
    f.date_key AS PeriodKey,
    'Municipal Debt' AS Domain,
    CASE WHEN d.is_fiscal_year_end
         THEN 'Municipal Arrears - Year End'
         ELSE 'Municipal Arrears - In Year' END AS Metric,
    f.gross_arrears_rand AS Value,
    'Rand' AS Unit,
    f.evidence_type AS EvidenceType,
    f.source_dataset_id AS SourceDatasetId
FROM fact_municipal_debt f
JOIN dim_date d USING (date_key)
WHERE f.municipality_key = 0
UNION ALL
SELECT date_key, 'Operations', 'Electricity Sales', sales_twh, 'TWh',
       'FACT_REPORTED', source_dataset_id
FROM fact_electricity_sales
WHERE segment_key = 0 AND sales_twh IS NOT NULL
UNION ALL
SELECT date_key, 'Financial', 'Electricity Revenue', revenue_rand, 'Rand',
       'FACT_REPORTED', 'DS007'
FROM fact_electricity_sales
WHERE segment_key = 0 AND revenue_rand IS NOT NULL
UNION ALL
SELECT date_key, domain, metric_name, metric_value, unit, evidence_type, source_dataset_id
FROM fact_corporate_metric
UNION ALL
SELECT f.reporting_date_key, 'Security', m.metric_name, f.metric_value, m.unit,
       f.evidence_type, f.source_dataset_id
FROM fact_security_metric f
JOIN dim_metric m USING (metric_key);

DROP VIEW IF EXISTS vw_powerbi_tariff;
CREATE VIEW vw_powerbi_tariff AS
SELECT
    effective_date_key AS PeriodKey,
    fiscal_year_label AS FiscalYear,
    customer_group AS CustomerGroup,
    increase_pct AS IncreasePct,
    intended_effective_date AS EffectiveDate,
    regulatory_status AS RegulatoryStatus,
    source_dataset_id AS SourceDatasetId,
    status_source_dataset_id AS StatusSourceDatasetId
FROM fact_tariff_adjustment;

DROP VIEW IF EXISTS vw_powerbi_scenario;
CREATE VIEW vw_powerbi_scenario AS
SELECT
    date_key AS PeriodKey,
    scenario_name AS ScenarioName,
    'Municipal Arrears' AS Metric,
    projected_arrears_rand AS Value,
    'Rand' AS Unit,
    evidence_type AS EvidenceType,
    source_dataset_id AS SourceDatasetId
FROM fact_municipal_debt_scenario;

DROP VIEW IF EXISTS vw_powerbi_source;
CREATE VIEW vw_powerbi_source AS
SELECT
    dataset_id AS DatasetId,
    metric AS Metric,
    source_publisher AS Publisher,
    source_tier AS SourceTier,
    publication_date AS PublicationDate,
    evidence_type AS EvidenceType,
    verification_status AS VerificationStatus,
    COALESCE(NULLIF(primary_source_url, ''), secondary_corroboration_url) AS SourceUrl,
    CASE WHEN source_tier IN ('A1', 'A2') THEN 1 ELSE 0 END AS IsPrimary
FROM stg_data_source_register;
