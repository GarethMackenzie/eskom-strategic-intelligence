"""Shared project paths and build settings."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = PROJECT_ROOT / "sql"
DOCS_DIR = PROJECT_ROOT / "docs"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATABASE_PATH = PROCESSED_DIR / "eskom_intelligence.sqlite"
QA_SUMMARY_PATH = PROCESSED_DIR / "qa_summary.json"
SOURCE_REGISTER_PATH = DOCS_DIR / "data_source_register.csv"

SCHEMA_SQL = (
    "03_dim_date.sql",
    "04_dim_municipality.sql",
    "05_dim_customer_segment.sql",
    "05b_dim_incident_location.sql",
    "05c_dim_legal_status_and_metric.sql",
    "06_fact_municipal_debt.sql",
    "07_fact_electricity_sales.sql",
    "08_fact_security.sql",
)

REPORTING_SQL = (
    "13_source_freshness.sql",
    "01_source_profiling.sql",
    "02_data_quality.sql",
    "09_debt_trends.sql",
    "10_sales_analysis.sql",
    "11_pareto_analysis.sql",
    "12_executive_kpis.sql",
)
