"""Build the editable, source-controlled Power BI Project (PBIP/PBIR/TMDL).

The semantic model uses small inline Power Query tables so the portfolio report
has no local-path dependency. All values are public, governed observations from
docs/data_source_register.csv. This generator is deterministic and safe for CI.
"""

from __future__ import annotations

import csv
import json
import textwrap
import uuid
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_NAME = "EskomStrategicIntelligence"
MEASURE_TABLE = "MeasureCatalog"
MODEL = ROOT / f"{PROJECT_NAME}.SemanticModel"
REPORT = ROOT / f"{PROJECT_NAME}.Report"
MODEL_DEF = MODEL / "definition"
REPORT_DEF = REPORT / "definition"
SOURCE_REGISTER = ROOT / "docs" / "data_source_register.csv"

SCHEMA_ROOT = "https://developer.microsoft.com/json-schemas/fabric/item"
COLORS = {
    "ink": "#071522",
    "panel": "#10283A",
    "line": "#244A5F",
    "teal": "#24C7B1",
    "blue": "#4D9DE0",
    "gold": "#F4B942",
    "coral": "#F06449",
    "white": "#EAF4F8",
    "muted": "#91A9B8",
}


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def stable_id(value: str) -> str:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"eskom-strategic-intelligence/{value}").hex[:20]


def quote_name(value: str) -> str:
    return f"'{value}'" if any(char in value for char in " -+%&/") else value


def m_value(value: object, data_type: str) -> str:
    if value is None or value == "":
        return "null"
    if data_type == "dateTime":
        parsed = date.fromisoformat(str(value))
        return f"#date({parsed.year}, {parsed.month}, {parsed.day})"
    if data_type in {"int64", "double", "decimal"}:
        return str(value)
    if data_type == "boolean":
        return "true" if value else "false"
    return '"' + str(value).replace('"', '""').replace("\r", " ").replace("\n", " ") + '"'


def table_tmdl(
    table_name: str,
    columns: list[tuple[str, str]],
    rows: list[tuple[object, ...]],
    *,
    key_columns: set[str] | None = None,
    hidden_columns: set[str] | None = None,
) -> str:
    key_columns = key_columns or set()
    hidden_columns = hidden_columns or set()
    m_types = {
        "int64": "Int64.Type",
        "double": "number",
        "decimal": "Currency.Type",
        "dateTime": "date",
        "string": "text",
        "boolean": "logical",
    }
    lines = [f"table {quote_name(table_name)}"]
    for name, data_type in columns:
        lines.extend([f"\tcolumn {quote_name(name)}", f"\t\tdataType: {data_type}"])
        if name in key_columns:
            lines.append("\t\tisKey")
        if name in hidden_columns:
            lines.append("\t\tisHidden")
        if data_type in {"int64", "double", "decimal"}:
            lines.append("\t\tsummarizeBy: none")
        if data_type == "dateTime":
            lines.append("\t\tformatString: yyyy-MM-dd")
        lines.append(f"\t\tsourceColumn: {name}")
        lines.append("")

    type_expression = ", ".join(
        f"{quote_name(name)} = {m_types[data_type]}" for name, data_type in columns
    )
    row_expressions = []
    for row in rows:
        values = ", ".join(
            m_value(value, data_type) for value, (_, data_type) in zip(row, columns)
        )
        row_expressions.append(f"\t\t\t\t{{{values}}}")
    lines.extend(
        [
            f"\tpartition {quote_name(table_name)} = m",
            "\t\tmode: import",
            "\t\tsource = ```",
            "\t\t\t#table(",
            f"\t\t\t\ttype table [{type_expression}],",
            "\t\t\t\t{",
            ",\n".join(row_expressions),
            "\t\t\t\t}",
            "\t\t\t)",
            "\t\t\t```",
            "",
            "\tannotation PBI_ResultType = Table",
            "",
        ]
    )
    return "\n".join(lines)


def dax_expression(value: str) -> str:
    if "\n" not in value:
        return value
    return "```\n" + textwrap.indent(value, "\t\t") + "\n\t```"


MEASURES = [
    ("Metric Value", "SUM ( FactMetric[Value] )", "#,0.00", "Base aggregation used only with a governed metric filter.", "Core"),
    ("Year-End Municipal Arrears", 'CALCULATE ( SUM ( FactMetric[Value] ), FactMetric[Metric] = "Municipal Arrears - Year End" )', "R0.0,,,bn", "Reported fiscal-year-end municipal arrears; non-additive across periods.", "Municipal Debt"),
    ("Latest Year-End Municipal Arrears", 'CALCULATE ( MAX ( FactMetric[Value] ), REMOVEFILTERS ( DimPeriod ), FactMetric[Metric] = "Municipal Arrears - Year End", FactMetric[PeriodKey] = 20260331 )', "R0.0,,,bn", "Latest governed fiscal-year-end balance: R111.6bn; intentionally unaffected by period slicers.", "Municipal Debt"),
    ("Latest In-Year Municipal Arrears", 'CALCULATE ( MAX ( FactMetric[Value] ), FactMetric[Metric] = "Municipal Arrears - In Year" )', "R0.0,,,bn", "Latest in-year observation: R119.9bn at June 2026; kept separate from year-end.", "Municipal Debt"),
    ("Municipal Arrears YoY %", "DIVIDE ( [Latest Year-End Municipal Arrears] - 94600000000, 94600000000 )", "0.0%", "FY2026 year-end change against the governed FY2025 comparator.", "Municipal Debt"),
    ("Scenario Municipal Arrears FY2031", "MAX ( FactScenario[Value] )", "R0.0,,,bn", "Eskom management no-intervention scenario; not a reported actual.", "Scenario"),
    ("Scenario Gap vs Latest", "[Scenario Municipal Arrears FY2031] - [Latest Year-End Municipal Arrears]", "R0.0,,,bn", "Scenario difference, not a forecast produced by this project.", "Scenario"),
    ("Electricity Sales", 'CALCULATE ( SUM ( FactMetric[Value] ), FactMetric[Metric] = "Electricity Sales" )', "0.0 TWh", "Reported annual electricity sales.", "Operations"),
    ("Latest Electricity Sales", 'CALCULATE ( MAX ( FactMetric[Value] ), REMOVEFILTERS ( DimPeriod ), FactMetric[Metric] = "Electricity Sales", FactMetric[PeriodKey] = 20260331 )', "0.0 TWh", "Latest reported annual sales: 178 TWh; intentionally unaffected by period slicers.", "Operations"),
    ("Sales YoY %", "DIVIDE ( [Latest Electricity Sales] - 189.7, 189.7 )", "0.0%", "FY2026 sales change versus FY2025.", "Operations"),
    ("Energy Availability Factor", 'DIVIDE ( CALCULATE ( SUM ( FactMetric[Value] ), FactMetric[Metric] = "Energy Availability Factor" ), 100 )', "0.00%", "Reported Energy Availability Factor by fiscal year.", "Operations"),
    ("Latest EAF", 'DIVIDE ( CALCULATE ( MAX ( FactMetric[Value] ), REMOVEFILTERS ( DimPeriod ), FactMetric[Metric] = "Energy Availability Factor", FactMetric[PeriodKey] = 20260331 ), 100 )', "0.00%", "Latest reported EAF: 65.16%; intentionally unaffected by period slicers.", "Operations"),
    ("EAF Change pp", "100 * [Latest EAF] - 60.6", "0.00 pp", "Percentage-point change versus FY2025.", "Operations"),
    ("Net Profit After Tax", 'CALCULATE ( MAX ( FactMetric[Value] ), FactMetric[Metric] = "Net Profit After Tax" )', "R0.0,,,bn", "Reported FY2026 net profit after tax.", "Financial"),
    ("Electricity Revenue", 'CALCULATE ( MAX ( FactMetric[Value] ), FactMetric[Metric] = "Electricity Revenue" )', "R0.0,,,bn", "FY2026 electricity revenue; secondary, corroborated evidence.", "Financial"),
    ("Security Losses", 'CALCULATE ( MAX ( FactMetric[Value] ), FactMetric[Metric] = "Security Losses" )', "R0.0,,m", "Aggregate physical-security losses, not coal-specific.", "Security"),
    ("Security Recoveries", 'CALCULATE ( MAX ( FactMetric[Value] ), FactMetric[Metric] = "Security Recoveries" )', "R0.0,,m", "Aggregate physical-security recoveries, not coal-specific.", "Security"),
    ("Security Recovery Rate", "DIVIDE ( [Security Recoveries], [Security Losses] )", "0.0%", "Recoveries divided by estimated losses; descriptive, not causal.", "Security"),
    ("Arrests", 'CALCULATE ( MAX ( FactMetric[Value] ), FactMetric[Metric] = "Arrests" )', "#,0", "Aggregate arrests in the physical-security disclosure.", "Security"),
    ("Convictions", 'CALCULATE ( MAX ( FactMetric[Value] ), FactMetric[Metric] = "Convictions" )', "#,0", "Aggregate convictions in the physical-security disclosure.", "Security"),
    ("Security Metric Value", 'CALCULATE ( SUM ( FactMetric[Value] ), FactMetric[Domain] = "Security" )', "#,0.00", "Security-only value used with the metric category; units remain visible in the evidence table.", "Security"),
    ("Tariff Increase %", "DIVIDE ( MAX ( FactTariff[IncreasePct] ), 100 )", "0.00%", "Average increase for the tariff row in filter context.", "Tariff"),
    ("FY2026/27 Direct Increase", 'DIVIDE ( CALCULATE ( MAX ( FactTariff[IncreasePct] ), FactTariff[CustomerGroup] = "Direct customers - average", FactTariff[FiscalYear] = "FY2026/27" ), 100 )', "0.00%", "Implemented average direct-customer increase from 1 April 2026.", "Tariff"),
    ("FY2026/27 Municipal Increase", 'DIVIDE ( CALCULATE ( MAX ( FactTariff[IncreasePct] ), FactTariff[CustomerGroup] = "Municipal bulk purchases" ), 100 )', "0.00%", "Implemented average municipal bulk increase from 1 July 2026.", "Tariff"),
    ("FY2027/28 Average Increase", 'DIVIDE ( CALCULATE ( MAX ( FactTariff[IncreasePct] ), FactTariff[CustomerGroup] = "Average price path" ), 100 )', "0.00%", "FY2027/28 average path; detailed retail structure remained under consultation at 4 September 2026.", "Tariff"),
    ("Illustrative Tariff Index", "100 * ( 1 + 0.1274 ) * ( 1 + 0.0876 ) * ( 1 + 0.0883 )", "0.0", "Mathematical index from the three average paths, baseline 100; not a customer bill forecast.", "Tariff"),
    ("Tariff Consultation Status", '"8.83% average path | retail structure under consultation at 04 Sep 2026"', "General", "Regulatory status label, not a claim of final customer-category tariffs.", "Tariff"),
    ("Governed Source Count", "COUNTROWS ( SourceRegister )", "#,0", "Number of governed source-register records embedded in the model.", "Governance"),
    ("Primary Source Count", 'CALCULATE ( COUNTROWS ( SourceRegister ), SourceRegister[IsPrimary] = TRUE () )', "#,0", "Direct official or primary-document source records (tier A1/A2).", "Governance"),
    ("Latest Evidence Date", 'FORMAT ( MAX ( SourceRegister[PublicationDate] ), "dd mmm yyyy" )', "General", "Latest reported evidence date excluding scenario horizons.", "Governance"),
]


def create_semantic_model() -> int:
    # Power BI rejects the reserved table name used by the earlier generator.
    (MODEL_DEF / "tables" / "Measures.tmdl").unlink(missing_ok=True)
    tables: dict[str, tuple[list[tuple[str, str]], list[tuple[object, ...]], set[str], set[str]]] = {
        "DimPeriod": (
            [("PeriodKey", "int64"), ("FiscalYear", "string"), ("EffectiveDate", "dateTime"), ("PeriodLabel", "string"), ("SortOrder", "int64")],
            [
                (20240331, "FY2024", "2024-03-31", "FY2024 year-end", 1),
                (20250331, "FY2025", "2025-03-31", "FY2025 year-end", 2),
                (20250401, "FY2025/26", "2025-04-01", "FY2025/26 tariff", 3),
                (20260331, "FY2026", "2026-03-31", "FY2026 year-end", 4),
                (20260401, "FY2026/27", "2026-04-01", "FY2026/27 direct tariff", 5),
                (20260630, "FY2026", "2026-06-30", "June 2026 in-year", 6),
                (20260701, "FY2026/27", "2026-07-01", "FY2026/27 municipal tariff", 7),
                (20270401, "FY2027/28", "2027-04-01", "FY2027/28 intended tariff", 8),
                (20310331, "FY2031", "2031-03-31", "FY2031 scenario", 9),
            ],
            {"PeriodKey"},
            {"PeriodKey", "SortOrder"},
        ),
        "FactMetric": (
            [("PeriodKey", "int64"), ("Domain", "string"), ("Metric", "string"), ("Value", "double"), ("Unit", "string"), ("EvidenceType", "string"), ("SourceDatasetId", "string")],
            [
                (20240331, "Municipal Debt", "Municipal Arrears - Year End", 55300000000, "Rand", "FACT_REPORTED", "DS031"),
                (20250331, "Municipal Debt", "Municipal Arrears - Year End", 94600000000, "Rand", "FACT_REPORTED", "DS031"),
                (20260331, "Municipal Debt", "Municipal Arrears - Year End", 111600000000, "Rand", "FACT_REPORTED", "DS001"),
                (20260630, "Municipal Debt", "Municipal Arrears - In Year", 119900000000, "Rand", "FACT_REPORTED", "DS002"),
                (20250331, "Operations", "Electricity Sales", 189.7, "TWh", "FACT_REPORTED", "DS006"),
                (20260331, "Operations", "Electricity Sales", 178.0, "TWh", "FACT_REPORTED", "DS006"),
                (20250331, "Operations", "Energy Availability Factor", 60.6, "Percent", "FACT_REPORTED", "DS012"),
                (20260331, "Operations", "Energy Availability Factor", 65.16, "Percent", "FACT_REPORTED", "DS012"),
                (20260331, "Financial", "Net Profit After Tax", 30300000000, "Rand", "FACT_REPORTED", "DS009"),
                (20260331, "Financial", "Electricity Revenue", 354700000000, "Rand", "FACT_REPORTED", "DS007"),
                (20260331, "Security", "Security Losses", 191000000, "Rand", "FACT_REPORTED", "DS015"),
                (20260331, "Security", "Security Recoveries", 34000000, "Rand", "FACT_REPORTED", "DS017"),
                (20260331, "Security", "Arrests", 505, "Count", "FACT_REPORTED", "DS016"),
                (20260331, "Security", "Convictions", 13, "Count", "FACT_REPORTED", "DS018"),
            ],
            set(),
            {"PeriodKey"},
        ),
        "FactTariff": (
            [("PeriodKey", "int64"), ("FiscalYear", "string"), ("CustomerGroup", "string"), ("IncreasePct", "double"), ("EffectiveDate", "dateTime"), ("RegulatoryStatus", "string"), ("SourceDatasetId", "string"), ("StatusSourceDatasetId", "string")],
            [
                (20250401, "FY2025/26", "Direct customers - average", 12.74, "2025-04-01", "Approved and implemented", "DS035", "DS035"),
                (20260401, "FY2026/27", "Direct customers - average", 8.76, "2026-04-01", "Approved and implemented", "DS036", "DS036"),
                (20260701, "FY2026/27", "Municipal bulk purchases", 9.01, "2026-07-01", "Approved and implemented", "DS036", "DS036"),
                (20270401, "FY2027/28", "Average price path", 8.83, "2027-04-01", "Average path established; retail structure and customer-category allocation under NERSA consultation at 2026-09-04", "DS035", "DS037"),
            ],
            set(),
            {"PeriodKey"},
        ),
        "FactScenario": (
            [("PeriodKey", "int64"), ("ScenarioName", "string"), ("Metric", "string"), ("Value", "double"), ("Unit", "string"), ("EvidenceType", "string"), ("SourceDatasetId", "string")],
            [(20310331, "No further intervention", "Municipal Arrears", 358000000000, "Rand", "SCENARIO_MANAGEMENT", "DS003")],
            set(),
            {"PeriodKey"},
        ),
    }

    with SOURCE_REGISTER.open(newline="", encoding="utf-8") as handle:
        sources = list(csv.DictReader(handle))
    source_rows = [
        (
            row["dataset_id"],
            row["metric"],
            row["source_publisher"],
            row["source_tier"],
            row["publication_date"],
            row["evidence_type"],
            row["verification_status"],
            row["primary_source_url"] or row["secondary_corroboration_url"],
            row["source_tier"] in {"A1", "A2"},
        )
        for row in sources
    ]
    tables["SourceRegister"] = (
        [("DatasetId", "string"), ("Metric", "string"), ("Publisher", "string"), ("SourceTier", "string"), ("PublicationDate", "dateTime"), ("EvidenceType", "string"), ("VerificationStatus", "string"), ("SourceUrl", "string"), ("IsPrimary", "boolean")],
        source_rows,
        {"DatasetId"},
        set(),
    )

    for table_name, (columns, rows, keys, hidden) in tables.items():
        write(
            MODEL_DEF / "tables" / f"{table_name}.tmdl",
            table_tmdl(table_name, columns, rows, key_columns=keys, hidden_columns=hidden),
        )

    measure_lines = [
        f"table {MEASURE_TABLE}",
        "\tcolumn Value",
        "\t\tdataType: int64",
        "\t\tisHidden",
        "\t\tsummarizeBy: none",
        "\t\tsourceColumn: Value",
        "",
    ]
    for name, expression, format_string, description, folder in MEASURES:
        measure_lines.extend(
            [
                f"\t/// {description}",
                f"\tmeasure {quote_name(name)} = {dax_expression(expression)}",
                f"\t\tformatString: {format_string}",
                f"\t\tdisplayFolder: {folder}",
                "",
            ]
        )
    measure_lines.extend(
        [
            f"\tpartition {MEASURE_TABLE} = m",
            "\t\tmode: import",
            "\t\tsource = #table(type table [Value = Int64.Type], {{1}})",
            "",
            "\tannotation PBI_ResultType = Table",
            "",
        ]
    )
    write(MODEL_DEF / "tables" / f"{MEASURE_TABLE}.tmdl", "\n".join(measure_lines))

    model_tables = [*tables, MEASURE_TABLE]
    model = [
        "model Model",
        "\tculture: en-ZA",
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tdiscourageImplicitMeasures",
        "\tsourceQueryCulture: en-ZA",
        "",
        "\tdataAccessOptions",
        "\t\tfastCombine",
        "\t\tlegacyRedirects",
        "\t\treturnErrorValuesAsNull",
        "",
        *[f"ref table {quote_name(table)}" for table in model_tables],
        "",
    ]
    write(MODEL_DEF / "model.tmdl", "\n".join(model))
    write(MODEL_DEF / "database.tmdl", "database\n\tcompatibilityLevel: 1600\n")

    relationships = [
        ("FactMetric.PeriodKey", "DimPeriod.PeriodKey"),
        ("FactTariff.PeriodKey", "DimPeriod.PeriodKey"),
        ("FactScenario.PeriodKey", "DimPeriod.PeriodKey"),
    ]
    relationship_lines: list[str] = []
    for index, (source, target) in enumerate(relationships, start=1):
        relationship_lines.extend(
            [
                f"relationship {stable_id(f'relationship-{index}')}",
                f"\tfromColumn: {source}",
                f"\ttoColumn: {target}",
                "",
            ]
        )
    write(MODEL_DEF / "relationships.tmdl", "\n".join(relationship_lines))
    write(
        MODEL_DEF / "roles.tmdl",
        """
        role Viewer
            modelPermission: read
        """,
    )
    return len(sources)


def column_field(table: str, column: str) -> dict:
    return {
        "field": {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": column}},
        "queryRef": f"{table}.{column}",
        "nativeQueryRef": column,
    }


def measure_field(name: str) -> dict:
    return {
        "field": {
            "Measure": {
                "Expression": {"SourceRef": {"Entity": MEASURE_TABLE}},
                "Property": name,
            }
        },
        "queryRef": f"{MEASURE_TABLE}.{name}",
        "nativeQueryRef": name,
    }


def title_config(title: str) -> dict:
    return {
        "title": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": "'" + title.replace("'", "''") + "'"}}},
                }
            }
        ]
    }


def visual_base(name: str, x: int, y: int, width: int, height: int, z: int) -> dict:
    return {
        "$schema": f"{SCHEMA_ROOT}/report/definition/visualContainer/2.9.0/schema.json",
        "name": name,
        "position": {"x": x, "y": y, "z": z, "height": height, "width": width, "tabOrder": z},
    }


def textbox(name: str, value: str, x: int, y: int, width: int, height: int, z: int) -> dict:
    result = visual_base(name, x, y, width, height, z)
    result["visual"] = {
        "visualType": "textbox",
        "objects": {"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": value}]}]}}]},
    }
    return result


def card(name: str, title: str, measure: str, x: int, y: int, width: int, height: int, z: int) -> dict:
    result = visual_base(name, x, y, width, height, z)
    result["visual"] = {
        "visualType": "card",
        "query": {"queryState": {"Values": {"projections": [measure_field(measure)]}}},
        "visualContainerObjects": title_config(title),
    }
    return result


def slicer(name: str, title: str, field: tuple[str, str], x: int, y: int, width: int, height: int, z: int) -> dict:
    result = visual_base(name, x, y, width, height, z)
    result["visual"] = {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [column_field(*field)]}}},
        "visualContainerObjects": title_config(title),
    }
    return result


def chart(name: str, visual_type: str, title: str, category: tuple[str, str], measure: str, x: int, y: int, width: int, height: int, z: int, series: tuple[str, str] | None = None) -> dict:
    state = {
        "Category": {"projections": [column_field(*category)]},
        "Y": {"projections": [measure_field(measure)]},
    }
    if series:
        state["Series"] = {"projections": [column_field(*series)]}
    result = visual_base(name, x, y, width, height, z)
    result["visual"] = {
        "visualType": visual_type,
        "query": {"queryState": state},
        "visualContainerObjects": title_config(title),
    }
    return result


def table_visual(name: str, title: str, fields: list[tuple[str, str]], x: int, y: int, width: int, height: int, z: int) -> dict:
    result = visual_base(name, x, y, width, height, z)
    result["visual"] = {
        "visualType": "tableEx",
        "query": {"queryState": {"Values": {"projections": [column_field(*field) for field in fields]}}},
        "visualContainerObjects": title_config(title),
    }
    return result


PAGES = [
    {
        "name": "Executive Overview",
        "slug": "executive-overview",
        "slicer": ("Fiscal period", ("DimPeriod", "FiscalYear")),
        "kpis": ["Latest Year-End Municipal Arrears", "Latest Electricity Sales", "Latest EAF", "Net Profit After Tax", "FY2027/28 Average Increase", "Governed Source Count"],
        "charts": [
            ("lineChart", "Municipal arrears at fiscal year-end", ("DimPeriod", "FiscalYear"), "Year-End Municipal Arrears", None),
            ("lineChart", "Electricity sales trend", ("DimPeriod", "FiscalYear"), "Electricity Sales", None),
            ("lineChart", "Energy Availability Factor", ("DimPeriod", "FiscalYear"), "Energy Availability Factor", None),
            ("clusteredColumnChart", "Tariff path by customer group", ("FactTariff", "FiscalYear"), "Tariff Increase %", ("FactTariff", "CustomerGroup")),
        ],
    },
    {
        "name": "Tariff & Affordability",
        "slug": "tariff-affordability",
        "slicer": ("Customer group", ("FactTariff", "CustomerGroup")),
        "kpis": ["FY2026/27 Direct Increase", "FY2026/27 Municipal Increase", "FY2027/28 Average Increase", "Illustrative Tariff Index", "Latest Electricity Sales", "Electricity Revenue"],
        "charts": [
            ("lineChart", "Average tariff path", ("FactTariff", "FiscalYear"), "Tariff Increase %", ("FactTariff", "CustomerGroup")),
            ("clusteredColumnChart", "Sales alongside tariff cycles", ("DimPeriod", "FiscalYear"), "Electricity Sales", None),
        ],
        "table": ("Regulatory status and lineage", [("FactTariff", "FiscalYear"), ("FactTariff", "CustomerGroup"), ("FactTariff", "IncreasePct"), ("FactTariff", "EffectiveDate"), ("FactTariff", "RegulatoryStatus"), ("FactTariff", "SourceDatasetId")]),
    },
    {
        "name": "Municipal Debt",
        "slug": "municipal-debt",
        "slicer": ("Fiscal period", ("DimPeriod", "FiscalYear")),
        "kpis": ["Latest Year-End Municipal Arrears", "Latest In-Year Municipal Arrears", "Municipal Arrears YoY %", "Scenario Municipal Arrears FY2031", "Scenario Gap vs Latest", "Governed Source Count"],
        "charts": [
            ("lineChart", "Reported fiscal-year-end arrears", ("DimPeriod", "FiscalYear"), "Year-End Municipal Arrears", None),
            ("clusteredColumnChart", "Reported vs management scenario", ("DimPeriod", "FiscalYear"), "Scenario Municipal Arrears FY2031", None),
        ],
        "table": ("Governed metric observations", [("FactMetric", "Domain"), ("FactMetric", "Metric"), ("FactMetric", "Value"), ("FactMetric", "Unit"), ("FactMetric", "EvidenceType"), ("FactMetric", "SourceDatasetId")]),
    },
    {
        "name": "Operations & Security",
        "slug": "operations-security",
        "slicer": ("Metric domain", ("FactMetric", "Domain")),
        "kpis": ["Latest Electricity Sales", "Sales YoY %", "Latest EAF", "EAF Change pp", "Security Losses", "Security Recovery Rate"],
        "charts": [
            ("lineChart", "Electricity sales", ("DimPeriod", "FiscalYear"), "Electricity Sales", None),
            ("lineChart", "Energy availability", ("DimPeriod", "FiscalYear"), "Energy Availability Factor", None),
            ("clusteredColumnChart", "Aggregate security metrics", ("FactMetric", "Metric"), "Security Metric Value", None),
        ],
        "table": ("Governed metric evidence — security rows are domain-labelled", [("FactMetric", "Domain"), ("FactMetric", "Metric"), ("FactMetric", "Value"), ("FactMetric", "Unit"), ("FactMetric", "SourceDatasetId")]),
    },
    {
        "name": "Data Governance",
        "slug": "data-governance",
        "slicer": ("Source tier", ("SourceRegister", "SourceTier")),
        "kpis": ["Governed Source Count", "Primary Source Count", "Latest Evidence Date", "FY2027/28 Average Increase", "Latest Year-End Municipal Arrears", "Latest EAF"],
        "charts": [
            ("donutChart", "Sources by evidence type", ("SourceRegister", "EvidenceType"), "Governed Source Count", None),
            ("clusteredBarChart", "Sources by tier", ("SourceRegister", "SourceTier"), "Governed Source Count", None),
        ],
        "table": ("Evidence register", [("SourceRegister", "DatasetId"), ("SourceRegister", "Metric"), ("SourceRegister", "Publisher"), ("SourceRegister", "SourceTier"), ("SourceRegister", "PublicationDate"), ("SourceRegister", "VerificationStatus")]),
    },
]


def create_report() -> tuple[int, int]:
    page_order: list[str] = []
    visual_count = 0
    nav = "EXECUTIVE  |  TARIFF & AFFORDABILITY  |  MUNICIPAL DEBT  |  OPERATIONS & SECURITY  |  DATA GOVERNANCE"
    for page in PAGES:
        page_id = stable_id(f"page-{page['slug']}")
        page_order.append(page_id)
        page_dir = REPORT_DEF / "pages" / page_id
        write_json(
            page_dir / "page.json",
            {
                "$schema": f"{SCHEMA_ROOT}/report/definition/page/2.1.0/schema.json",
                "name": page_id,
                "displayName": page["name"],
                "displayOption": "FitToPage",
                "height": 720,
                "width": 1280,
            },
        )
        visuals: list[dict] = []
        z = 1
        visuals.append(textbox(stable_id(f"{page_id}-title"), f"ESKOM STRATEGIC INTELLIGENCE  |  {page['name']}", 20, 12, 1240, 38, z)); z += 1
        visuals.append(textbox(stable_id(f"{page_id}-nav"), nav, 20, 54, 990, 28, z)); z += 1
        slicer_title, slicer_field = page["slicer"]
        visuals.append(slicer(stable_id(f"{page_id}-slicer"), slicer_title, slicer_field, 1020, 50, 240, 40, z)); z += 1
        for index, metric in enumerate(page["kpis"]):
            visuals.append(card(stable_id(f"{page_id}-kpi-{index}"), metric, metric, 20 + index * 205, 94, 190, 118, z)); z += 1
        charts = page["charts"]
        chart_columns = 2 if len(charts) in {2, 4} else 3
        chart_width = 600 if chart_columns == 2 else 395
        chart_height = 165 if len(charts) == 4 else 195
        chart_x_step = 620 if chart_columns == 2 else 415
        chart_y_step = 180 if len(charts) == 4 else 210
        for index, (visual_type, title, category, metric, series) in enumerate(charts):
            x = 20 + (index % chart_columns) * chart_x_step
            y = 232 + (index // chart_columns) * chart_y_step
            visuals.append(chart(stable_id(f"{page_id}-chart-{index}"), visual_type, title, category, metric, x, y, chart_width, chart_height, z, series)); z += 1
        if "table" in page:
            table_title, fields = page["table"]
            visuals.append(table_visual(stable_id(f"{page_id}-table"), table_title, fields, 20, 445, 1240, 210, z)); z += 1
        elif len(charts) >= 3:
            insight_y = 592 if len(charts) == 4 else 452
            insight_height = 60 if len(charts) == 4 else 72
            visuals.append(textbox(stable_id(f"{page_id}-insight"), "Decision lens: separate reported actuals, derived indicators and management scenarios before interpreting the trend.", 20, insight_y, 1240, insight_height, z)); z += 1
        disclosure = "PUBLIC-DATA PORTFOLIO PROJECT  •  NO CUSTOMER OR OPERATIONAL DATA  •  SOURCE-VALIDATED 04 SEP 2026  •  POWER BI DESKTOP/SERVICE RUNTIME STATUS IN docs/POWER_BI_RUNBOOK.md"
        if page["slug"] == "tariff-affordability":
            disclosure = "8.83% = FY2027/28 AVERAGE PATH  •  RETAIL STRUCTURE/CUSTOMER ALLOCATION UNDER NERSA CONSULTATION AT 04 SEP 2026  •  INDEX IS NOT A BILL FORECAST"
        if page["slug"] == "operations-security":
            disclosure = "SECURITY FIGURES ARE AGGREGATE PHYSICAL-SECURITY METRICS  •  THEY ARE NOT COAL-SPECIFIC  •  ASSOCIATION IS NOT CAUSATION"
        visuals.append(textbox(stable_id(f"{page_id}-footer"), disclosure, 20, 676, 1240, 26, z))
        for visual in visuals:
            write_json(page_dir / "visuals" / visual["name"] / "visual.json", visual)
        visual_count += len(visuals)

    write_json(
        REPORT_DEF / "pages" / "pages.json",
        {
            "$schema": f"{SCHEMA_ROOT}/report/definition/pagesMetadata/1.0.0/schema.json",
            "pageOrder": page_order,
            "activePageName": page_order[0],
        },
    )
    return len(page_order), visual_count


def create_foundation() -> None:
    write_json(
        ROOT / f"{PROJECT_NAME}.pbip",
        {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
            "version": "1.0",
            "artifacts": [{"report": {"path": f"{PROJECT_NAME}.Report"}}],
            "settings": {"enableAutoRecovery": True},
        },
    )
    write_json(
        REPORT / "definition.pbir",
        {
            "$schema": f"{SCHEMA_ROOT}/report/definitionProperties/2.0.0/schema.json",
            "version": "4.0",
            "datasetReference": {"byPath": {"path": f"../{PROJECT_NAME}.SemanticModel"}},
        },
    )
    write_json(
        MODEL / "definition.pbism",
        {
            "$schema": f"{SCHEMA_ROOT}/semanticModel/definitionProperties/1.0.0/schema.json",
            "version": "4.2",
            "settings": {"qnaEnabled": True},
        },
    )
    write_json(
        REPORT_DEF / "version.json",
        {"$schema": f"{SCHEMA_ROOT}/report/definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"},
    )
    theme_name = "EskomStrategicIntelligenceTheme"
    write_json(
        REPORT_DEF / "report.json",
        {
            "$schema": f"{SCHEMA_ROOT}/report/definition/report/3.2.0/schema.json",
            "themeCollection": {"customTheme": {"name": theme_name, "reportVersionAtImport": {"visual": "2.9.0", "report": "3.2.0", "page": "2.1.0"}, "type": "RegisteredResources"}},
            "filterConfig": {"filters": []},
            "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources", "items": [{"name": theme_name, "path": "eskom-intelligence-theme.json", "type": "CustomTheme"}]}],
            "settings": {"useStylableVisualContainerHeader": True, "defaultFilterActionIsDataFilter": True, "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True, "allowInlineExploration": True, "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True},
            "slowDataSourceSettings": {"isCrossHighlightingDisabled": False, "isSlicerSelectionsButtonEnabled": False, "isFilterSelectionsButtonEnabled": False, "isFieldWellButtonEnabled": False, "isApplyAllButtonEnabled": False},
        },
    )
    theme = {
        "name": "Eskom Strategic Intelligence",
        "dataColors": [COLORS["teal"], COLORS["blue"], COLORS["gold"], COLORS["coral"], "#7FB069", "#8E7DBE"],
        "background": COLORS["ink"],
        "foreground": COLORS["white"],
        "tableAccent": COLORS["teal"],
        "good": COLORS["teal"],
        "neutral": COLORS["gold"],
        "bad": COLORS["coral"],
        "textClasses": {
            "title": {"fontFace": "Segoe UI Semibold", "fontSize": 15, "color": COLORS["white"]},
            "header": {"fontFace": "Segoe UI Semibold", "fontSize": 11, "color": COLORS["white"]},
            "label": {"fontFace": "Segoe UI", "fontSize": 10, "color": COLORS["muted"]},
            "callout": {"fontFace": "Segoe UI Semibold", "fontSize": 24, "color": COLORS["white"]},
        },
        "visualStyles": {"*": {"*": {"background": [{"color": {"solid": {"color": COLORS["panel"]}}, "transparency": 2}], "border": [{"show": True, "color": {"solid": {"color": COLORS["line"]}}, "radius": 8}], "title": [{"show": True, "fontFace": "Segoe UI Semibold", "fontSize": 11, "fontColor": {"solid": {"color": COLORS["white"]}}}], "visualHeader": [{"show": True, "foreground": {"solid": {"color": COLORS["muted"]}}}]}}, "page": {"*": {"background": [{"color": {"solid": {"color": COLORS["ink"]}}, "transparency": 0}]}}},
    }
    write_json(REPORT / "StaticResources" / "RegisteredResources" / "eskom-intelligence-theme.json", theme)


def create_preview() -> None:
    values = [55.3, 94.6, 111.6]
    bars = []
    for index, (label, value) in enumerate(zip(["FY2024", "FY2025", "FY2026"], values)):
        height = value / max(values) * 170
        x = 720 + index * 120
        y = 540 - height
        bars.append(f'<rect x="{x}" y="{y:.0f}" width="70" height="{height:.0f}" rx="5" fill="{COLORS["teal"]}"/><text x="{x + 35}" y="{y - 10:.0f}" text-anchor="middle" class="small">R{value:.1f}bn</text><text x="{x + 35}" y="570" text-anchor="middle" class="muted">{label}</text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
    <style>.title{{font:700 28px 'Segoe UI';fill:{COLORS['white']}}}.sub{{font:14px 'Segoe UI';fill:{COLORS['muted']}}}.k{{font:600 13px 'Segoe UI';fill:{COLORS['muted']}}}.v{{font:700 26px 'Segoe UI';fill:{COLORS['white']}}}.small{{font:600 13px 'Segoe UI';fill:{COLORS['white']}}}.muted{{font:12px 'Segoe UI';fill:{COLORS['muted']}}}</style>
    <rect width="1280" height="720" fill="{COLORS['ink']}"/><text x="42" y="58" class="title">ESKOM STRATEGIC INTELLIGENCE</text><text x="42" y="86" class="sub">Power BI Project preview • governed public evidence • as at 04 September 2026</text>
    <rect x="42" y="112" width="1196" height="2" fill="{COLORS['teal']}"/>
    <g>{''.join(f'<rect x="{42+i*196}" y="142" width="180" height="112" rx="10" fill="{COLORS["panel"]}" stroke="{COLORS["line"]}"/><text x="{58+i*196}" y="174" class="k">{label}</text><text x="{58+i*196}" y="218" class="v">{value}</text>' for i,(label,value) in enumerate([('YEAR-END ARREARS','R111.6bn'),('ELECTRICITY SALES','178 TWh'),('EAF','65.16%'),('NET PROFIT','R30.3bn'),('FY2027/28 PATH','8.83%'),('GOVERNED SOURCES','38')]))}</g>
    <rect x="42" y="286" width="590" height="320" rx="12" fill="{COLORS['panel']}" stroke="{COLORS['line']}"/><text x="66" y="322" class="small">TARIFF PATH & REGULATORY STATUS</text>
    <text x="66" y="378" class="v" fill="{COLORS['gold']}">8.83%</text><text x="66" y="408" class="small">FY2027/28 average price path</text><text x="66" y="446" class="sub">Intended effective date: 01 April 2027</text><text x="66" y="476" class="sub">Retail tariff structure and customer-category allocation</text><text x="66" y="502" class="sub">under NERSA consultation at 04 September 2026.</text><rect x="66" y="536" width="230" height="36" rx="18" fill="{COLORS['gold']}"/><text x="181" y="560" text-anchor="middle" style="font:700 13px 'Segoe UI';fill:{COLORS['ink']}">STATUS: CONSULTATION</text>
    <rect x="654" y="286" width="584" height="320" rx="12" fill="{COLORS['panel']}" stroke="{COLORS['line']}"/><text x="678" y="322" class="small">MUNICIPAL ARREARS • FISCAL YEAR-END</text>{''.join(bars)}
    <text x="42" y="660" class="muted">Source-controlled PBIP • PBIR report • TMDL semantic model • automated QA • no private operational data</text><text x="42" y="684" class="muted">Preview only: interactive rendering requires Power BI Desktop or publication to Power BI Service.</text></svg>'''
    write(ROOT / "assets" / "eskom-power-bi-preview.svg", svg)


def main() -> dict[str, int]:
    create_foundation()
    source_count = create_semantic_model()
    pages, visuals = create_report()
    create_preview()
    summary = {"pages": pages, "visuals": visuals, "measures": len(MEASURES), "sources": source_count}
    print(f"PASS: Power BI Project generated ({pages} pages, {visuals} visuals, {len(MEASURES)} measures, {source_count} sources)")
    return summary


if __name__ == "__main__":
    main()
