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
        _empty_query(
            connection,
            "tariff_missing_lineage",
            """SELECT effective_date_key FROM fact_tariff_adjustment
               WHERE source_dataset_id IS NULL OR status_source_dataset_id IS NULL""",
        ),
        _empty_query(
            connection,
            "tariff_rate_range",
            """SELECT effective_date_key FROM fact_tariff_adjustment
               WHERE increase_pct <= 0 OR increase_pct >= 100""",
        ),
        _empty_query(
            connection,
            "municipal_debt_source_orphans",
            """SELECT f.source_dataset_id FROM fact_municipal_debt f
               LEFT JOIN stg_data_source_register s ON f.source_dataset_id=s.dataset_id
               WHERE s.dataset_id IS NULL""",
        ),
        _empty_query(
            connection,
            "annual_debt_series_shape",
            """SELECT 1 WHERE
               (SELECT COUNT(*) FROM fact_municipal_debt f JOIN dim_date d USING(date_key)
                WHERE f.municipality_key=0 AND d.is_fiscal_year_end=TRUE) <> 12
               OR (SELECT MIN(d.fiscal_year) FROM fact_municipal_debt f JOIN dim_date d USING(date_key)
                   WHERE f.municipality_key=0 AND d.is_fiscal_year_end=TRUE) <> 2015
               OR (SELECT MAX(d.fiscal_year) FROM fact_municipal_debt f JOIN dim_date d USING(date_key)
                   WHERE f.municipality_key=0 AND d.is_fiscal_year_end=TRUE) <> 2026""",
        ),
        _empty_query(
            connection,
            "fy2024_total_arrears",
            """SELECT date_key FROM fact_municipal_debt
               WHERE municipality_key=0 AND date_key=20240331
                 AND gross_arrears_rand <> 74400000000""",
        ),
        _empty_query(
            connection,
            "relief_scope_not_total_arrears",
            """SELECT 1 WHERE
               (SELECT approved_legacy_debt_rand FROM fact_municipal_debt_relief_programme
                WHERE programme_name='Municipal Debt Relief Programme') <> 55300000000
               OR EXISTS (SELECT 1 FROM fact_municipal_debt
                          WHERE municipality_key=0 AND gross_arrears_rand=55300000000)""",
        ),
        _empty_query(
            connection,
            "semantic_export_lineage",
            """SELECT p.SourceDatasetId FROM vw_powerbi_metric p
               LEFT JOIN stg_data_source_register s ON p.SourceDatasetId=s.dataset_id
               WHERE s.dataset_id IS NULL""",
        ),
        _empty_query(
            connection,
            "source_url_scheme",
            """SELECT dataset_id FROM stg_data_source_register
               WHERE COALESCE(NULLIF(primary_source_url,''), secondary_corroboration_url)
                     NOT LIKE 'http%'""",
        ),
    ]

    freshness = connection.execute(
        "SELECT data_reported_as_of FROM vw_report_freshness"
    ).fetchone()[0]
    expected_freshness = connection.execute("""
        SELECT MAX(date(publication_date))
        FROM stg_data_source_register
        WHERE evidence_type NOT LIKE 'SCENARIO%'
          AND LOWER(verification_status) NOT LIKE '%superseded%'
    """).fetchone()[0]
    checks.append(
        CheckResult(
            "report_freshness",
            freshness == expected_freshness,
            f"latest actual disclosure date={freshness}; expected={expected_freshness}",
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
