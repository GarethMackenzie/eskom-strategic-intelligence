"""Build the analytical database and write the QA summary."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.build_database import build_database  # noqa: E402
from src.config import DATABASE_PATH, QA_SUMMARY_PATH  # noqa: E402
from src.validation.quality import run_quality_checks, serialise_results  # noqa: E402
from build_powerbi_project import main as build_powerbi_project  # noqa: E402


def main() -> int:
    power_bi = build_powerbi_project()
    connection, source_count = build_database(DATABASE_PATH)
    try:
        results = run_quality_checks(connection)
    finally:
        connection.close()

    summary = serialise_results(results)
    summary["source_records"] = source_count
    summary["database"] = str(DATABASE_PATH.relative_to(PROJECT_ROOT))
    summary["power_bi"] = power_bi
    QA_SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    for result in results:
        print(f"{'PASS' if result.passed else 'FAIL'}: {result.name} ({result.detail})")
    print(f"{summary['status']}: {len(results)} build-time checks; {source_count} governed sources")
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
