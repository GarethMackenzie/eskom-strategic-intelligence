-- ============================================================================
-- 08_fact_security.sql
-- Rebuilds the flawed Phase-1 fact_security_incidents / fact_security_case_log
-- design per docs/technical_audit.md P0-2 and P1-1.
--
-- Three structures replace the old single table:
--   1. fact_security_metric      -- one row per (reporting_date, incident_scope,
--                                    metric, location); own source_dataset_id
--                                    per metric, not one shared ID for five
--                                    disclosures.
--   2. fact_security_case         -- one row per named, individually-sourced
--                                    incident (Camden, Tutuka, etc.)
--   3. fact_security_case_event   -- chronological legal-process events per
--                                    case (arrest -> charge -> conviction ->
--                                    sentence), so history is never destroyed
--                                    by overwriting a single status field.
--
-- The NATJOINTS R1.09m cluster (previously mis-modelled as one case-log row
-- with legal_status='Mixed...') is corrected to live in fact_security_metric,
-- because it is an aggregate financial-impact observation across multiple
-- unrelated cases, not a single traceable case -- see DS028 notes.
-- ============================================================================

-- ---- 1. Metric-level lineage (fixes P1-1) ---------------------------------
DROP TABLE IF EXISTS fact_security_metric;
CREATE TABLE fact_security_metric (
    reporting_date_key    INTEGER NOT NULL REFERENCES dim_date(date_key),
    incident_type_key       INTEGER NOT NULL REFERENCES dim_incident_type(incident_type_key),
    metric_key                 INTEGER NOT NULL REFERENCES dim_metric(metric_key),
    location_key                  INTEGER NOT NULL REFERENCES dim_location(location_key),
    metric_value                     NUMERIC(18,2) NOT NULL,
    source_dataset_id                    VARCHAR(10) NOT NULL,     -- one metric, one source. No sharing.
    evidence_type                           VARCHAR(30) NOT NULL DEFAULT 'FACT_REPORTED',
    PRIMARY KEY (reporting_date_key, incident_type_key, metric_key, location_key)
);

-- FY2026 AGGREGATE physical-security disclosure -- five metrics, five
-- distinct source_dataset_id values even though all five currently trace to
-- the same underlying press release, because that reflects the disclosure
-- reality (they COULD diverge on a future refresh) and satisfies Step 4's
-- "every displayed number must resolve to its exact source" requirement at
-- the metric grain rather than the article grain.
INSERT INTO fact_security_metric (reporting_date_key, incident_type_key, metric_key, location_key, metric_value, source_dataset_id) VALUES
(20260331, 0, 1, 0, -13.00, 'DS014'),   -- Incident Count YoY Change (%)
(20260331, 0, 2, 0, 191000000.00, 'DS015'),  -- Estimated Financial Loss (Rand)
(20260331, 0, 3, 0, 505, 'DS016'),      -- Arrests (Count)
(20260331, 0, 4, 0, 34000000.00, 'DS017'),   -- Recoveries (Rand)
(20260331, 0, 5, 0, 13, 'DS018'),       -- Convictions (Count)
(20260331, 0, 6, 0, -18.00, 'DS015'),   -- Estimated Financial Loss YoY Change (%) -- distinct metric_key, own row, no PK collision
(20260331, 0, 7, 0, 38.00, 'DS017'),    -- Recoveries YoY Change (%)
(20260331, 0, 8, 0, 18.00, 'DS016');    -- Arrests YoY Change (%)
-- NATJOINTS-coordinated cluster financial impact (DS028) -- an aggregate
-- financial-impact observation spanning multiple unrelated case types
-- (extortion, theft, diesel theft, procurement fraud per the source
-- article), NOT a single case. Modelled here as metric-level observations,
-- correcting the Phase-1 error of storing it as one case-log row with a
-- composite legal_status string.
INSERT INTO fact_security_metric (reporting_date_key, incident_type_key, metric_key, location_key, metric_value, source_dataset_id) VALUES
(20250331, 0, 2, 0, 1090000.00, 'DS028'),   -- Estimated Financial Loss, NATJOINTS cluster, as at Mar 2025
(20250331, 0, 4, 0, 873000.00, 'DS028');    -- Recoveries, NATJOINTS cluster, as at Mar 2025
-- Modelled at incident_type_key=0 (aggregate) because DS028's own source
-- states the cluster spans multiple, unspecified case types -- assigning a
-- single specific incident type would misrepresent the source.

-- ---- 2. Individually-sourced case register (fixes P0-2) -------------------
DROP TABLE IF EXISTS fact_security_case;
CREATE TABLE fact_security_case (
    case_id             INTEGER PRIMARY KEY,
    case_title          VARCHAR(150) NOT NULL,
    location_key         INTEGER NOT NULL REFERENCES dim_location(location_key),
    incident_type_key       INTEGER NOT NULL REFERENCES dim_incident_type(incident_type_key),
    opened_date                DATE,                 -- earliest date evidenced by the source; NULL if not stated
    source_dataset_id             VARCHAR(10) NOT NULL,  -- the SPECIFIC article/release describing THIS case
    case_summary                     VARCHAR(400) NOT NULL
);

INSERT INTO fact_security_case VALUES
(1, 'Camden Power Station heavy-fuel-oil theft', 1, 4, '2024-08-21', 'DS026',
 'Four Eskom employees and a contractor security guard arrested after a 30,610kg truck carrying stolen heavy fuel oil was intercepted at the Camden weighbridge; the driver fled the scene.'),
(2, 'Tutuka Power Station dome-valve theft', 4, 11, '2023-01-01', 'DS027',
 'An Eskom supplier and his brother arrested for theft of 16 dome valves (R173,000) from Tutuka Power Station; investigation traced back to 2023, arrests reported 5 March 2025. Opened date is an approximation (year only) per source imprecision -- do not treat as exact.');

-- ---- 3. Chronological legal-process events per case (fixes P1-2) ---------
DROP TABLE IF EXISTS fact_security_case_event;
CREATE TABLE fact_security_case_event (
    event_id             INTEGER PRIMARY KEY,
    case_id                INTEGER NOT NULL REFERENCES fact_security_case(case_id),
    event_date               DATE NOT NULL,
    legal_status_key            INTEGER NOT NULL REFERENCES dim_legal_status(legal_status_key),
    financial_impact_rand           NUMERIC(18,2),      -- NULL if not officially stated
    recovered_rand                     NUMERIC(18,2),   -- NULL if not officially stated
    source_dataset_id                     VARCHAR(10) NOT NULL,
    event_notes                              VARCHAR(300)
);

INSERT INTO fact_security_case_event VALUES
(1, 1, '2024-08-21', 3, NULL, NULL, 'DS026', 'Arrest event -- financial impact of the stolen fuel oil load not officially quantified in the source release.'),
(2, 2, '2025-03-05', 3, 173000.00, NULL, 'DS027', 'Arrest event -- R173,000 is the stated value of the stolen dome valves; no recovery amount stated.');

-- Deliberately NO further events (Charge/Conviction/Sentence) are inserted
-- for either case: no source located in this pass confirms those subsequent
-- legal-process stages occurred. This is the correct, honest state -- an
-- open case is left open, not advanced to a status the evidence doesn't
-- support (see docs/technical_audit.md and the project's non-negotiable
-- data-integrity rule against converting an allegation into a conviction).
