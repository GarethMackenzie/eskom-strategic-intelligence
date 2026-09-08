"""
tests/test_data_quality.py

Automated data-quality and release tests. Builds the same complete SQLite
database used by the project command and asserts the governed integrity rules.
Run with:

    python3 -m pytest tests/test_data_quality.py -v

or directly:

    python3 tests/test_data_quality.py

All shipped SQL targets SQLite and is executed during every database build.
"""

import csv
import os
import re
import sys
from pathlib import Path

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.analytics.build_database import build_database  # noqa: E402

SQL_DIR = os.path.join(REPO_ROOT, "sql")
DOCS_DIR = os.path.join(REPO_ROOT, "docs")


def build_db():
    conn, _ = build_database()
    return conn


def load_source_register():
    path = os.path.join(DOCS_DIR, "data_source_register.csv")
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_no_duplicate_fact_primary_keys():
    conn = build_db()
    cur = conn.cursor()
    checks = {
        "fact_municipal_debt": ["date_key", "municipality_key"],
        "fact_electricity_sales": ["date_key", "segment_key"],
        "fact_security_metric": [
            "reporting_date_key",
            "incident_type_key",
            "metric_key",
            "location_key",
        ],
        "fact_municipal_debt_scenario": ["date_key", "scenario_name"],
    }
    for table, keys in checks.items():
        cols = ", ".join(keys)
        cur.execute(f"SELECT {cols}, COUNT(*) c FROM {table} GROUP BY {cols} HAVING COUNT(*) > 1")
        dupes = cur.fetchall()
        assert dupes == [], f"Duplicate PK in {table}: {dupes}"
    print("PASS: no duplicate fact primary keys")


def test_no_orphan_dimension_keys():
    conn = build_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT f.* FROM fact_municipal_debt f
        LEFT JOIN dim_date d ON f.date_key = d.date_key
        LEFT JOIN dim_municipality m ON f.municipality_key = m.municipality_key
        WHERE d.date_key IS NULL OR m.municipality_key IS NULL
    """)
    orphans = cur.fetchall()
    assert orphans == [], f"Orphaned fact_municipal_debt rows: {orphans}"
    print("PASS: no orphan dimension keys in fact_municipal_debt")


def test_every_fact_observation_has_source_lineage():
    conn = build_db()
    cur = conn.cursor()
    for table in [
        "fact_municipal_debt",
        "fact_electricity_sales",
        "fact_security_metric",
        "fact_municipal_debt_scenario",
    ]:
        cur.execute(
            f"SELECT COUNT(*) FROM {table} WHERE source_dataset_id IS NULL OR source_dataset_id = ''"
        )
        n = cur.fetchone()[0]
        assert n == 0, f"{table} has {n} rows with missing source_dataset_id"
    print("PASS: every fact row has a non-null source_dataset_id")


def test_no_secondary_url_classified_primary():
    """Every row with source_tier in (A1, A2) must NOT have an empty
    primary_source_url, and every row with an empty primary_source_url must
    NOT be tier A1/A2. Catches the exact Phase-1 defect (P0-1)."""
    rows = load_source_register()
    violations = []
    for r in rows:
        tier = r["source_tier"].strip()
        primary_url = r["primary_source_url"].strip()
        if tier in ("A1", "A2") and not primary_url:
            violations.append((r["dataset_id"], "tier A but no primary_source_url"))
    assert violations == [], f"Source-tier integrity violations: {violations}"
    print(f"PASS: no secondary-only source classified A1/A2 ({len(rows)} sources checked)")


def test_no_scenario_row_in_actuals_table():
    conn = build_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM fact_municipal_debt WHERE evidence_type LIKE 'SCENARIO%'")
    n = cur.fetchone()[0]
    assert n == 0, f"Found {n} scenario-classified rows inside the actuals fact table"
    print("PASS: no scenario row present in fact_municipal_debt")


def test_latest_reported_debt_resolves_correctly():
    """Reproduces the P0-3 fix: the 'latest' resolution logic must return the
    single most recent observation, NOT a sum of all historical balances."""
    conn = build_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT SUM(gross_arrears_rand) FROM fact_municipal_debt WHERE municipality_key = 0"
    )
    naive_sum = cur.fetchone()[0]
    cur.execute("""
        SELECT gross_arrears_rand FROM fact_municipal_debt
        WHERE municipality_key = 0 ORDER BY date_key DESC LIMIT 1
    """)
    latest = cur.fetchone()[0]
    assert latest == 119900000000.00, f"Expected latest = R119.9bn, got {latest}"
    assert naive_sum != latest, (
        "Sanity check: naive SUM should differ from latest (else test is vacuous)"
    )
    print(
        f"PASS: latest-resolution logic returns R{latest / 1e9:.1f}bn, correctly distinct from naive SUM R{naive_sum / 1e9:.1f}bn"
    )


def test_data_as_of_cannot_resolve_to_scenario_date():
    conn = build_db()
    cur = conn.cursor()
    cur.execute("SELECT MAX(calendar_date) FROM dim_date WHERE is_scenario_horizon = 0")
    max_actual_date = cur.fetchone()[0]
    assert max_actual_date != "2031-03-31", "Data-As-Of logic resolved to the scenario horizon date"
    cur.execute("SELECT MAX(calendar_date) FROM dim_date")
    max_any_date = cur.fetchone()[0]
    assert max_any_date == "2031-03-31", "Sanity check: scenario date should exist in dim_date"
    print(f"PASS: scenario-excluded max date = {max_actual_date} (correctly excludes 2031-03-31)")


def test_source_freshness_uses_latest_actual_disclosure():
    conn = build_db()
    actual = conn.execute("SELECT data_reported_as_of FROM vw_report_freshness").fetchone()[0]
    expected = conn.execute("""
        SELECT MAX(date(publication_date)) FROM stg_data_source_register
        WHERE evidence_type NOT LIKE 'SCENARIO%'
          AND LOWER(verification_status) NOT LIKE '%superseded%'
    """).fetchone()[0]
    assert actual == expected, f"Expected source-derived {expected}, got {actual}"
    leaked = conn.execute("""
        SELECT r.dataset_id
        FROM fact_source_refresh r
        JOIN stg_data_source_register s USING (dataset_id)
        WHERE s.evidence_type LIKE 'SCENARIO%'
    """).fetchall()
    assert leaked == [], f"Scenario sources leaked into freshness: {leaked}"
    print(f"PASS: freshness resolves dynamically to {actual} and excludes scenarios")


def test_all_sql_files_execute_in_release_build():
    """The full builder executes every shipped SQL file before returning."""
    conn = build_db()
    expected_objects = {
        "stg_data_source_register",
        "fact_municipal_debt",
        "fact_source_refresh",
        "vw_report_freshness",
        "vw_executive_kpis_actual",
        "vw_executive_kpis_scenario",
        "fact_tariff_adjustment",
        "vw_tariff_path",
    }
    actual_objects = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')")
    }
    assert expected_objects <= actual_objects, expected_objects - actual_objects
    print("PASS: complete release SQL stack executes and creates governed objects")


def test_current_fiscal_year_end_debt_is_not_latest_in_year_snapshot():
    conn = build_db()
    latest_year_end = conn.execute("""
        SELECT f.gross_arrears_rand
        FROM fact_municipal_debt f
        JOIN dim_date d USING (date_key)
        WHERE f.municipality_key=0 AND d.is_fiscal_year_end=TRUE
        ORDER BY f.date_key DESC LIMIT 1
    """).fetchone()[0]
    latest_any = conn.execute("""
        SELECT gross_arrears_rand FROM fact_municipal_debt
        WHERE municipality_key=0 ORDER BY date_key DESC LIMIT 1
    """).fetchone()[0]
    assert latest_year_end == 111600000000
    assert latest_any == 119900000000

    dax = (Path(REPO_ROOT) / "powerbi" / "dax" / "measures.dax").read_text(encoding="utf-8")
    yoy_block = dax.split("Municipal Arrears YoY % =", 1)[1].split(
        "Municipal Arrears Long-Run CAGR =", 1
    )[0]
    assert "[Latest Year-End Municipal Arrears]" in yoy_block
    assert "[Prior Year-End Municipal Arrears]" in yoy_block
    assert "119900000000" not in yoy_block
    print("PASS: fiscal-year comparison uses R111.6bn, not the R119.9bn in-year snapshot")


def test_source_register_ids_unique_and_evidence_atomic():
    rows = load_source_register()
    ids = [row["dataset_id"] for row in rows]
    assert len(ids) == len(set(ids)), "Duplicate dataset_id in source register"
    allowed = {
        "FACT_REPORTED",
        "CALCULATION_DERIVED",
        "INTERPRETATION_ONLY",
        "SCENARIO_MANAGEMENT",
        "SCENARIO_PROJECT",
    }
    invalid = [
        (row["dataset_id"], row["evidence_type"])
        for row in rows
        if row["evidence_type"] not in allowed
    ]
    assert invalid == [], f"Non-atomic/invalid evidence types: {invalid}"
    print(f"PASS: {len(rows)} unique source IDs with atomic evidence classifications")


def test_no_retired_schema_references_in_data_quality_sql():
    sql = (Path(SQL_DIR) / "02_data_quality.sql").read_text(encoding="utf-8")
    retired = ["fact_security_case_log", "is_scenario =", "WHERE status LIKE"]
    found = [token for token in retired if token in sql]
    assert found == [], f"Retired schema references remain: {found}"
    print("PASS: data-quality SQL contains no retired Phase-1 schema references")


def test_no_local_paths_or_secret_assignments_in_tracked_text():
    root = Path(REPO_ROOT)
    excluded = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".test-deps",
        "test_dependencies",
    }
    path_pattern = re.compile(r"(?:[A-Za-z]:\\Users\\|/Users/|/home/)", re.IGNORECASE)
    secret_pattern = re.compile(
        r"(?i)(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*['\"][^'\"]{8,}"
    )
    findings = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part in excluded for part in path.parts):
            continue
        if path.resolve() == Path(__file__).resolve():
            continue  # this test necessarily contains the detection patterns
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pbix", ".sqlite"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if path_pattern.search(text) or secret_pattern.search(text):
            findings.append(str(path.relative_to(root)))
    assert findings == [], f"Potential local path or secret material: {findings}"
    print("PASS: no local user paths or credential assignments found")


def test_municipality_balances_not_negative():
    conn = build_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM fact_municipal_debt WHERE gross_arrears_rand < 0")
    negatives = cur.fetchall()
    assert negatives == [], f"Found negative arrears balances: {negatives}"
    print("PASS: no negative municipal-debt balances")


def test_no_security_case_has_invalid_legal_status():
    conn = build_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT e.event_id FROM fact_security_case_event e
        LEFT JOIN dim_legal_status ls ON e.legal_status_key = ls.legal_status_key
        WHERE ls.legal_status_key IS NULL
    """)
    invalid = cur.fetchall()
    assert invalid == [], f"Security case events with invalid legal_status_key: {invalid}"
    # Also confirm no composite/free-text status strings exist anywhere in the table
    cur.execute("PRAGMA table_info(fact_security_case_event)")
    cols = [c[1] for c in cur.fetchall()]
    assert "legal_status" not in cols, "Legacy composite legal_status text column should not exist"
    print("PASS: all security case events have a valid, atomic legal_status_key")


def test_no_case_source_shared_across_unrelated_cases():
    """Reproduces the P0-2 fix: each case in fact_security_case must have its
    own source_dataset_id, and no two DIFFERENT cases should share the same
    source_dataset_id (which was the Phase-1 defect: DS019 reused across
    three unrelated cases)."""
    conn = build_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT source_dataset_id, COUNT(*) c, GROUP_CONCAT(case_title) FROM fact_security_case GROUP BY source_dataset_id HAVING COUNT(*) > 1"
    )
    shared = cur.fetchall()
    assert shared == [], f"Multiple unrelated cases share one source_dataset_id: {shared}"
    print("PASS: every security case has its own distinct source_dataset_id")


def test_metric_yoy_not_summed_as_level():
    """Guards against the P2 DAX bug class: a metric flagged as 'Percent' unit
    must never be aggregated with SUM across more than one reporting period in
    a way that would be presented as a single meaningful total. This test
    checks the current single-period state holds (n=1 row per YoY metric) so
    that a future second period addition is caught by this test failing,
    forcing a review of the aggregation logic before it ships."""
    conn = build_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.metric_name, COUNT(*) c FROM fact_security_metric f
        JOIN dim_metric m ON f.metric_key = m.metric_key
        WHERE m.unit = 'Percent'
        GROUP BY m.metric_name
        HAVING COUNT(*) > 1
    """)
    multi_period_percent_metrics = cur.fetchall()
    assert multi_period_percent_metrics == [], (
        f"Percent-unit metrics now have >1 period: {multi_period_percent_metrics}. "
        "Review Crime Incidents YoY %-style DAX measures before this ships -- "
        "a SUM over multiple periods of a percentage is invalid."
    )
    print("PASS: no percent-unit security metric has more than one period (SUM-safety check)")


def test_tariff_path_preserves_regulatory_status():
    conn = build_db()
    row = conn.execute("""
        SELECT increase_pct, regulatory_status, intended_effective_date,
               source_dataset_id, status_source_dataset_id
        FROM fact_tariff_adjustment
        WHERE fiscal_year_label='FY2027/28' AND customer_group='Average price path'
    """).fetchone()
    assert row is not None
    assert row[0] == 8.83
    assert row[2] == "2027-04-01"
    assert row[3:] == ("DS035", "DS037")
    assert "consultation" in row[1].lower()
    assert "final customer-category allocation" not in row[1].lower()
    print("PASS: 8.83% path is present with consultation status and dual-source lineage")


def test_canonical_annual_municipal_debt_series():
    conn = build_db()
    actual = conn.execute("""
        SELECT d.fiscal_year, f.gross_arrears_rand / 1000000000.0
        FROM fact_municipal_debt f JOIN dim_date d USING (date_key)
        WHERE f.municipality_key=0 AND d.is_fiscal_year_end=TRUE
        ORDER BY d.fiscal_year
    """).fetchall()
    expected = list(
        zip(
            range(2015, 2027),
            [5.0, 6.0, 9.4, 13.6, 19.9, 28.0, 35.3, 44.8, 58.5, 74.4, 94.6, 111.6],
            strict=True,
        )
    )
    assert actual == expected


def test_debt_relief_scope_cannot_leak_into_annual_total():
    conn = build_db()
    relief = conn.execute("""
        SELECT approved_legacy_debt_rand, approved_municipalities
        FROM fact_municipal_debt_relief_programme
    """).fetchone()
    assert relief == (55300000000, 71)
    assert (
        conn.execute("""
        SELECT COUNT(*) FROM fact_municipal_debt
        WHERE municipality_key=0 AND gross_arrears_rand=55300000000
    """).fetchone()[0]
        == 0
    )
    objects = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "fact_municipal_debt_alternate_estimate" not in objects


ALL_TESTS = [
    test_no_duplicate_fact_primary_keys,
    test_no_orphan_dimension_keys,
    test_every_fact_observation_has_source_lineage,
    test_no_secondary_url_classified_primary,
    test_no_scenario_row_in_actuals_table,
    test_latest_reported_debt_resolves_correctly,
    test_data_as_of_cannot_resolve_to_scenario_date,
    test_source_freshness_uses_latest_actual_disclosure,
    test_all_sql_files_execute_in_release_build,
    test_current_fiscal_year_end_debt_is_not_latest_in_year_snapshot,
    test_source_register_ids_unique_and_evidence_atomic,
    test_no_retired_schema_references_in_data_quality_sql,
    test_no_local_paths_or_secret_assignments_in_tracked_text,
    test_municipality_balances_not_negative,
    test_no_security_case_has_invalid_legal_status,
    test_no_case_source_shared_across_unrelated_cases,
    test_metric_yoy_not_summed_as_level,
    test_tariff_path_preserves_regulatory_status,
    test_canonical_annual_municipal_debt_series,
    test_debt_relief_scope_cannot_leak_into_annual_total,
]

if __name__ == "__main__":
    failures = 0
    for t in ALL_TESTS:
        try:
            t()
        except AssertionError as e:
            failures += 1
            print(f"FAIL: {t.__name__}: {e}")
    print(f"\n{len(ALL_TESTS) - failures}/{len(ALL_TESTS)} tests passed")
    sys.exit(1 if failures else 0)
