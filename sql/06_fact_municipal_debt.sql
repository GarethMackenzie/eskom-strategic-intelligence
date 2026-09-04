-- ============================================================================
-- 06_fact_municipal_debt.sql
-- Grain: one row per (date_key, municipality_key). Every row traceable to
-- docs/data_source_register.csv via source_dataset_id. Idempotent (safe to
-- re-run: DROP...CREATE, no ALTER mid-script).
--
-- FIXES APPLIED (see docs/technical_audit.md):
-- P0-5: scenario rows physically moved to fact_municipal_debt_scenario, a
--       separate table with no shared grain a naive SUM could pull in.
-- P1-3: status semantics corrected. A group-total row (municipality_key=0)
--       represents an AGGREGATE EXPOSURE, not one municipality's operational
--       delinquency status -- 'Delinquent' as a single label for R111.6bn
--       spread across hundreds of municipalities in different states is
--       misleading. Individual, named municipalities (e.g. City of
--       Johannesburg) retain a genuine operational status because that is
--       what the source actually supports for that one entity.
-- ============================================================================

DROP TABLE IF EXISTS dim_debt_status;
CREATE TABLE dim_debt_status (
    debt_status_key    INTEGER PRIMARY KEY,
    debt_status_name    VARCHAR(50) NOT NULL,
    applies_to_grain       VARCHAR(20) NOT NULL   -- 'Group-Total' or 'Individual Municipality'
);

INSERT INTO dim_debt_status (debt_status_key, debt_status_name, applies_to_grain) VALUES
(1, 'Aggregate Exposure (mixed underlying status)', 'Group-Total'),
(2, 'Delinquent', 'Individual Municipality'),
(3, 'Settled', 'Individual Municipality'),
(4, 'Current / Compliant', 'Individual Municipality');

DROP TABLE IF EXISTS fact_municipal_debt;
CREATE TABLE fact_municipal_debt (
    date_key                INTEGER NOT NULL REFERENCES dim_date(date_key),
    municipality_key         INTEGER NOT NULL REFERENCES dim_municipality(municipality_key),
    gross_arrears_rand        NUMERIC(18,2) NOT NULL CHECK (gross_arrears_rand >= 0),
    write_off_rand              NUMERIC(18,2),
    debt_status_key                INTEGER NOT NULL REFERENCES dim_debt_status(debt_status_key),
    evidence_type                     VARCHAR(30) NOT NULL DEFAULT 'FACT_REPORTED',
    calculation_method                   VARCHAR(200),   -- populated only for evidence_type = CALCULATION_DERIVED
    source_dataset_id                       VARCHAR(10) NOT NULL,
    PRIMARY KEY (date_key, municipality_key)
);

-- Group-total year-end position, FY2026 -- AGGREGATE EXPOSURE, not a single
-- delinquency status (fixes P1-3).
INSERT INTO fact_municipal_debt VALUES
(20260331, 0, 111600000000.00, 3600000000.00, 1, 'FACT_REPORTED', NULL, 'DS001');

-- Group-total FY2025 comparator. UPDATED IN PHASE 2: Phase 1 stored this as a
-- CALCULATION_DERIVED back-solve (R111.6bn / 1.179). This pass located an
-- INDEPENDENTLY REPORTED figure for the same date (National Treasury
-- MTBPS-sourced, DS031: R94.6bn) that happens to match the back-solved value
-- almost exactly -- corroboration, not coincidence assumed. Reclassified
-- FACT_REPORTED on that basis, citing DS031 as primary support with the
-- original back-solve retained in calculation_method for transparency.
-- NOTE: a second source (DS029, PMG committee testimony) gives a materially
-- different pairing (~R74bn Mar2024 -> ~R95bn Mar2025) for adjacent dates --
-- see docs/limitations.md "Reconciliation Item" for the unresolved conflict.
-- This row uses the Treasury/MTBPS figure because it independently
-- corroborates the Eskom-disclosed growth rate; the PMG figure is retained
-- separately in fact_municipal_debt_alternate_estimate for transparency.
INSERT INTO fact_municipal_debt VALUES
(20250331, 0, 94600000000.00, NULL, 1, 'FACT_REPORTED',
 'Corroborated by two independent methods: (1) Eskom-disclosed 17.9% YoY growth rate applied to FY2026 R111.6bn (DS001) backwards = R94.6bn; (2) National Treasury MTBPS-sourced figure for the same date (DS031) = R94.6bn. Both agree, raising confidence despite each individually being tier B/derived.',
 'DS031');

-- NEW IN PHASE 2: genuine third annual point, FY2024 year-end (31 March
-- 2024), closing part of Data Gap #4. Sourced from National Treasury
-- MTBPS-reporting via DS031.
INSERT INTO fact_municipal_debt VALUES
(20240331, 0, 55300000000.00, NULL, 1, 'FACT_REPORTED', NULL, 'DS031');


-- Group-total in-year management disclosure, June 2026 -- aggregate exposure,
-- non-year-end (see dim_date.observation_type).
INSERT INTO fact_municipal_debt VALUES
(20260630, 0, 119900000000.00, NULL, 1, 'FACT_REPORTED', NULL, 'DS002');

-- City of Johannesburg / City Power: genuine individual operational status
-- (delinquent at PAJA-notice balance date).
INSERT INTO fact_municipal_debt VALUES
(20260630, 1, 5255421994.16, NULL, 2, 'FACT_REPORTED', NULL, 'DS020');

-- City of Johannesburg / City Power: SETTLED as at 2026-08-21 (status-critical
-- row -- see docs/status_history_municipal_debt.csv for the human-readable
-- narrative version of this same fact).
INSERT INTO fact_municipal_debt VALUES
(20260821, 1, 0.00, NULL, 3, 'FACT_REPORTED', NULL, 'DS020');

-- ---------------------------------------------------------------------------
-- SCENARIO rows: physically separate table (fixes P0-5). No shared primary
-- key or grain with fact_municipal_debt, so a plain SUM/JOIN against the
-- actuals table cannot accidentally pull a scenario row in. Any query that
-- wants to show a scenario must explicitly reference this table by name.
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_municipal_debt_scenario;
CREATE TABLE fact_municipal_debt_scenario (
    date_key                INTEGER NOT NULL REFERENCES dim_date(date_key),
    scenario_name              VARCHAR(50) NOT NULL,   -- e.g. 'No Intervention (Eskom Management)'
    projected_arrears_rand        NUMERIC(18,2) NOT NULL,
    evidence_type                    VARCHAR(30) NOT NULL DEFAULT 'SCENARIO_MANAGEMENT',
    assumptions                         VARCHAR(400),
    source_dataset_id                      VARCHAR(10) NOT NULL,
    PRIMARY KEY (date_key, scenario_name)
);

INSERT INTO fact_municipal_debt_scenario VALUES
(20310331, 'No Intervention (Eskom Management)', 358000000000.00, 'SCENARIO_MANAGEMENT',
 'Eskom management''s stated projection absent decisive intervention (DS003, direct official release -- see data_source_register.csv). Not a project-generated projection. No underlying growth-rate model was disclosed alongside this figure, so it cannot be independently reconstructed or stress-tested; it is carried as a single terminal value, not a trajectory.',
 'DS003');

-- ---------------------------------------------------------------------------
-- Alternate estimate table (Phase 2 addition): holds the CONFLICTING PMG
-- committee-testimony figures for the same reporting dates as the
-- Treasury/MTBPS-sourced figures above. Deliberately NOT merged or
-- reconciled -- see docs/limitations.md "Reconciliation Item #1". A
-- reviewer/analyst can see both figures side by side rather than the
-- project silently picking a winner.
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_municipal_debt_alternate_estimate;
CREATE TABLE fact_municipal_debt_alternate_estimate (
    date_key                INTEGER NOT NULL REFERENCES dim_date(date_key),
    gross_arrears_rand        NUMERIC(18,2) NOT NULL,
    estimate_label               VARCHAR(80) NOT NULL,
    source_dataset_id               VARCHAR(10) NOT NULL,
    reconciliation_note                VARCHAR(300) NOT NULL,
    PRIMARY KEY (date_key, estimate_label)
);

INSERT INTO fact_municipal_debt_alternate_estimate VALUES
(20240331, 74000000000.00, 'Eskom CFO PMG committee testimony (approx.)', 'DS029',
 'Conflicts with fact_municipal_debt''s R55.3bn FY2024 figure (DS031, Treasury/MTBPS-sourced) by ~R18.7bn. Not reconciled in this pass -- see docs/limitations.md.'),
(20250331, 95000000000.00, 'Eskom CFO PMG committee testimony (approx.)', 'DS029',
 'Close to but not identical to fact_municipal_debt''s R94.6bn FY2025 figure (DS031) -- ~R0.4bn difference, within plausible rounding of verbal committee testimony ("approximately").');

-- ---------------------------------------------------------------------------
-- Provincial concentration (Phase 2 addition): PARTIALLY closes Data Gap #1
-- at province grain (full municipality-level ranking remains unavailable).
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS fact_municipal_debt_provincial;
CREATE TABLE fact_municipal_debt_provincial (
    date_key                INTEGER NOT NULL REFERENCES dim_date(date_key),
    province_key              INTEGER NOT NULL REFERENCES dim_province(province_key),
    gross_arrears_rand          NUMERIC(18,2) NOT NULL,
    rank_among_reported            INTEGER,   -- only meaningful among the provinces this source
                                                -- actually reported (2 of 9) -- NOT a complete
                                                -- provincial ranking
    source_dataset_id                 VARCHAR(10) NOT NULL,
    PRIMARY KEY (date_key, province_key)
);

-- Only 2 of 9 provinces individually reported in the source (DS030) -- the
-- remaining 7 are NOT populated with zero or estimated values; they are
-- simply absent, which is the honest representation of what is known.
INSERT INTO fact_municipal_debt_provincial VALUES
(20260717, 6, 30500000000.00, 1, 'DS030'),   -- Mpumalanga (province_key=6)
(20260717, 2, 29100000000.00, 2, 'DS030');   -- Free State (province_key=2)
