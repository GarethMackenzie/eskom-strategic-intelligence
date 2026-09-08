-- ============================================================================
-- 03_dim_date.sql
-- Eskom fiscal year: 1 April (Y-1) to 31 March (Y). Seeded at fiscal
-- year-end / disclosure-event grain because that is the grain of every
-- currently-sourced fact (see docs/limitations.md Data Gap #4 for why this
-- isn't daily/monthly).
--
-- FIX (Step 6 / Step 9 remediation): the FY2031 scenario horizon date now
-- lives here, in the dimension layer, not inserted mid-way through a fact
-- script as in Phase 1. It is flagged is_scenario_horizon = TRUE so that any
-- "Data As Of" / MAX(calendar_date) style logic can explicitly exclude it --
-- see powerbi/dax/measures.dax `Data Reported As Of` and
-- sql/13_source_freshness.sql for the enforcement mechanism.
-- ============================================================================

DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date (
    date_key                INTEGER PRIMARY KEY,   -- YYYYMMDD
    calendar_date             DATE NOT NULL,
    fiscal_year                 INTEGER NOT NULL,
    fiscal_year_label             VARCHAR(6) NOT NULL,
    is_fiscal_year_end              BOOLEAN NOT NULL DEFAULT FALSE,
    is_scenario_horizon                BOOLEAN NOT NULL DEFAULT FALSE,  -- TRUE only for
                                                                          -- forward scenario dates
                                                                          -- that must never drive
                                                                          -- "Data As Of" logic
    observation_type                      VARCHAR(30) NOT NULL,  -- 'Year-End Reported',
                                                                    -- 'In-Year Management Disclosure',
                                                                    -- 'Event-Driven', 'Scenario Horizon'
    source_dataset_id                       VARCHAR(10)
);

INSERT INTO dim_date (date_key, calendar_date, fiscal_year, fiscal_year_label, is_fiscal_year_end, is_scenario_horizon, observation_type, source_dataset_id) VALUES
(20150331, '2015-03-31', 2015, 'FY2015', TRUE,  FALSE, 'Year-End Reported', 'DS038'),
(20160331, '2016-03-31', 2016, 'FY2016', TRUE,  FALSE, 'Year-End Reported', 'DS038'),
(20170331, '2017-03-31', 2017, 'FY2017', TRUE,  FALSE, 'Year-End Reported', 'DS038'),
(20180331, '2018-03-31', 2018, 'FY2018', TRUE,  FALSE, 'Year-End Reported', 'DS038'),
(20190331, '2019-03-31', 2019, 'FY2019', TRUE,  FALSE, 'Year-End Reported', 'DS038'),
(20200331, '2020-03-31', 2020, 'FY2020', TRUE,  FALSE, 'Year-End Reported', 'DS038'),
(20210331, '2021-03-31', 2021, 'FY2021', TRUE,  FALSE, 'Year-End Reported', 'DS038'),
(20220331, '2022-03-31', 2022, 'FY2022', TRUE,  FALSE, 'Year-End Reported', 'DS038'),
(20230331, '2023-03-31', 2023, 'FY2023', TRUE,  FALSE, 'Year-End Reported', 'DS038'),
(20240331, '2024-03-31', 2024, 'FY2024', TRUE,  FALSE, 'Year-End Reported', 'DS038'),
(20250401, '2025-04-01', 2026, 'FY2025/26', FALSE, FALSE, 'Tariff Effective Date', 'DS035'),
(20250331, '2025-03-31', 2025, 'FY2025', TRUE,  FALSE, 'Year-End Reported', 'DS006'),
(20260331, '2026-03-31', 2026, 'FY2026', TRUE,  FALSE, 'Year-End Reported', 'DS001'),
(20260401, '2026-04-01', 2027, 'FY2026/27', FALSE, FALSE, 'Tariff Effective Date', 'DS036'),
(20260630, '2026-06-30', 2026, 'FY2026', FALSE, FALSE, 'In-Year Management Disclosure', 'DS002'),
(20260701, '2026-07-01', 2027, 'FY2026/27', FALSE, FALSE, 'Tariff Effective Date', 'DS036'),
(20260717, '2026-07-17', 2026, 'FY2026', FALSE, FALSE, 'Event-Driven', 'DS030'),
(20260821, '2026-08-21', 2026, 'FY2026', FALSE, FALSE, 'Event-Driven', 'DS020'),
(20260902, '2026-09-02', 2027, 'FY2026/27', FALSE, FALSE, 'Regulatory Consultation Update', 'DS037'),
(20270401, '2027-04-01', 2028, 'FY2027/28', FALSE, FALSE, 'Intended Tariff Effective Date', 'DS035'),
(20310331, '2031-03-31', 2031, 'FY2031', TRUE,  TRUE,  'Scenario Horizon', 'DS003');
