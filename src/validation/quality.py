"""Executable data-quality checks used by the build and CI."""

import sqlite3
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str


def _empty_query(connection: sqlite3.Connection, name: str, sql: str) -> CheckResult:
    rows = connection.execute(sql).fetchall()
    return CheckResult(name, not rows, f"{len(rows)} violation(s)")


def run_quality_checks(connection: sqlite3.Connection) -> list[CheckResult]:
    """Run the release-blocking integrity checks."""
    checks = [
        _empty_query(
            connection,
            "municipal_debt_duplicate_keys",
            """SELECT date_key, municipality_key FROM fact_municipal_debt
               GROUP BY date_key, municipality_key HAVING COUNT(*) > 1""",
        ),
        _empty_query(
            connection,
            "municipal_debt_orphans",
            """SELECT f.date_key FROM fact_municipal_debt f
               LEFT JOIN dim_date d ON f.date_key=d.date_key
               LEFT JOIN dim_municipality m ON f.municipality_key=m.municipality_key
               WHERE d.date_key IS NULL OR m.municipality_key IS NULL""",
        ),
        _empty_query(
            connection,
            "negative_municipal_debt",
            "SELECT date_key FROM fact_municipal_debt WHERE gross_arrears_rand < 0",
        ),
        _empty_query(
            connection,
            "scenario_in_actuals",
            "SELECT date_key FROM fact_municipal_debt WHERE evidence_type LIKE 'SCENARIO%'",
        ),
        _empty_query(
            connection,
            "sales_unit_range",
            "SELECT date_key FROM fact_electricity_sales WHERE sales_twh NOT BETWEEN 10 AND 500",
        ),
        _empty_query(
            connection,
            "duplicate_security_cases",
            """SELECT location_key, opened_date, case_summary FROM fact_security_case
               GROUP BY location_key, opened_date, case_summary HAVING COUNT(*) > 1""",
        ),
        _empty_query(
            connection,
            "tier_a_without_primary_url",
            """SELECT dataset_id FROM stg_data_source_register
               WHERE source_tier IN ('A1','A2') AND TRIM(primary_source_url) = ''""",
        ),
        _empty_query(
            connection,
            "scenario_in_freshness",
            """SELECT r.dataset_id FROM fact_source_refresh r
               JOIN stg_data_source_register s ON r.dataset_id=s.dataset_id
               WHERE s.evidence_type LIKE 'SCENARIO%'""",
        ),
    ]

    freshness = connection.execute(
        "SELECT data_reported_as_of FROM vw_report_freshness"
    ).fetchone()[0]
    checks.append(
        CheckResult(
            "report_freshness",
            freshness == "2026-08-31",
            f"latest actual disclosure date={freshness}",
        )
    )
    return checks


def serialise_results(results: list[CheckResult]) -> dict[str, object]:
    """Return JSON-ready QA output."""
    return {
        "status": "PASS" if all(item.passed for item in results) else "FAIL",
        "checks_run": len(results),
        "checks": [asdict(item) for item in results],
    }
