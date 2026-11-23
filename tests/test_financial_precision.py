import math
from pathlib import Path

import pytest

from src.analytics.build_database import build_database


def test_actual_and_scenario_billions_preserve_fraction():
    db, _ = build_database()
    try:
        value = db.execute(
            "SELECT kpi_value FROM vw_executive_kpis_actual WHERE kpi_name LIKE 'Municipal arrears%'"
        ).fetchone()[0]
        assert float(value) == pytest.approx(119.9)
        rows = db.execute(
            "SELECT v.projected_arrears_r_billion, f.projected_arrears_rand "
            "FROM vw_executive_kpis_scenario v JOIN fact_municipal_debt_scenario f "
            "USING (scenario_name)"
        ).fetchall()
        assert rows
        for billions, rand in rows:
            assert billions * 1_000_000_000 == pytest.approx(rand)
    finally:
        db.close()


def test_shipped_cagr_query_matches_independent_log_calculation():
    db, _ = build_database()
    try:
        sql = (Path(__file__).parents[1] / "sql/09_debt_trends.sql").read_text()
        query = "WITH annual AS (" + sql.split("WITH annual AS (", 1)[1].split(";", 1)[0]
        first_year, last_year, first, last, actual = db.execute(query).fetchone()
        expected = round(
            math.expm1((math.log(last) - math.log(first)) / (last_year - first_year)) * 100, 2
        )
        assert actual == pytest.approx(expected)
        db.execute(
            "UPDATE fact_municipal_debt SET gross_arrears_rand=0 "
            "WHERE municipality_key=0 AND date_key=(SELECT MIN(f.date_key) "
            "FROM fact_municipal_debt f JOIN dim_date d USING(date_key) "
            "WHERE municipality_key=0 AND d.is_fiscal_year_end=TRUE)"
        )
        assert db.execute(query).fetchone()[-1] is None
    finally:
        db.close()
