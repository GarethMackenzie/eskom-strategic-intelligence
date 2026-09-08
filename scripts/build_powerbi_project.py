"""Build the editable, source-controlled Power BI Project (PBIP/PBIR/TMDL).

The semantic model uses small inline Power Query tables so the portfolio report
has no local-path dependency. All values are public, governed observations from
docs/data_source_register.csv. This generator is deterministic and safe for CI.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
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
            m_value(value, data_type) for value, (_, data_type) in zip(row, columns, strict=True)
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


LATEST_VALUE = """VAR LatestPeriod =
    MAXX ( FILTER ( ALL ( FactMetric ), FactMetric[Metric] = \"{metric}\" ), FactMetric[PeriodKey] )
RETURN
    CALCULATE ( MAX ( FactMetric[Value] ), REMOVEFILTERS ( DimPeriod ),
        FactMetric[Metric] = \"{metric}\", FactMetric[PeriodKey] = LatestPeriod )"""

PRIOR_VALUE = """VAR LatestPeriod =
    MAXX ( FILTER ( ALL ( FactMetric ), FactMetric[Metric] = \"{metric}\" ), FactMetric[PeriodKey] )
VAR PriorPeriod =
    MAXX ( FILTER ( ALL ( FactMetric ), FactMetric[Metric] = \"{metric}\" && FactMetric[PeriodKey] < LatestPeriod ), FactMetric[PeriodKey] )
RETURN
    CALCULATE ( MAX ( FactMetric[Value] ), REMOVEFILTERS ( DimPeriod ),
        FactMetric[Metric] = \"{metric}\", FactMetric[PeriodKey] = PriorPeriod )"""

# Single semantic-measure catalog. Both TMDL and powerbi/dax/measures.dax are
# generated from this list; the generated DAX file is never edited by hand.
MEASURES = [
    (
        "Metric Value",
        "SUM ( FactMetric[Value] )",
        "#,0.00",
        "Base aggregation used only with a governed metric filter.",
        "Core",
    ),
    (
        "Year-End Municipal Arrears",
        'CALCULATE ( SUM ( FactMetric[Value] ), FactMetric[Metric] = "Municipal Arrears - Year End" )',
        "R0.0,,,bn",
        "Reported fiscal-year-end municipal arrears; non-additive across periods.",
        "Municipal Debt",
    ),
    (
        "Latest Year-End Municipal Arrears",
        LATEST_VALUE.format(metric="Municipal Arrears - Year End"),
        "R0.0,,,bn",
        "Latest governed fiscal-year-end balance selected dynamically.",
        "Municipal Debt",
    ),
    (
        "Prior Year-End Municipal Arrears",
        PRIOR_VALUE.format(metric="Municipal Arrears - Year End"),
        "R0.0,,,bn",
        "Immediate prior fiscal-year-end comparator selected dynamically.",
        "Municipal Debt",
    ),
    (
        "Latest In-Year Municipal Arrears",
        LATEST_VALUE.format(metric="Municipal Arrears - In Year"),
        "R0.0,,,bn",
        "Latest governed in-year balance, kept separate from year-end.",
        "Municipal Debt",
    ),
    (
        "Municipal Arrears YoY %",
        "DIVIDE ( [Latest Year-End Municipal Arrears] - [Prior Year-End Municipal Arrears], [Prior Year-End Municipal Arrears] )",
        "0.0%",
        "Latest year-end change against the dynamically selected prior year-end.",
        "Municipal Debt",
    ),
    (
        "Municipal Arrears Long-Run CAGR",
        """VAR DebtRows = FILTER ( ALL ( FactMetric ), FactMetric[Metric] = \"Municipal Arrears - Year End\" )
VAR EarliestDebtDate = MINX ( DebtRows, RELATED ( DimPeriod[EffectiveDate] ) )
VAR LatestDebtDate = MAXX ( DebtRows, RELATED ( DimPeriod[EffectiveDate] ) )
VAR EarliestDebtValue = MAXX ( FILTER ( DebtRows, RELATED ( DimPeriod[EffectiveDate] ) = EarliestDebtDate ), FactMetric[Value] )
VAR LatestDebtValue = MAXX ( FILTER ( DebtRows, RELATED ( DimPeriod[EffectiveDate] ) = LatestDebtDate ), FactMetric[Value] )
VAR ElapsedYears = DATEDIFF ( EarliestDebtDate, LatestDebtDate, YEAR )
RETURN IF ( ElapsedYears > 0, POWER ( DIVIDE ( LatestDebtValue, EarliestDebtValue ), DIVIDE ( 1, ElapsedYears ) ) - 1 )""",
        "0.0%",
        "CAGR from the earliest to latest comparable fiscal-year-end observation.",
        "Municipal Debt",
    ),
    (
        "Scenario Municipal Arrears FY2031",
        "MAX ( FactScenario[Value] )",
        "R0.0,,,bn",
        "Eskom management no-intervention scenario; not a reported actual.",
        "Scenario",
    ),
    (
        "Scenario Gap vs Latest",
        "[Scenario Municipal Arrears FY2031] - [Latest Year-End Municipal Arrears]",
        "R0.0,,,bn",
        "Scenario difference, not a forecast produced by this project.",
        "Scenario",
    ),
    (
        "Electricity Sales",
        'CALCULATE ( SUM ( FactMetric[Value] ), FactMetric[Metric] = "Electricity Sales" )',
        "0.0 TWh",
        "Reported annual electricity sales.",
        "Operations",
    ),
    (
        "Latest Electricity Sales",
        LATEST_VALUE.format(metric="Electricity Sales"),
        "0.0 TWh",
        "Latest reported annual sales selected dynamically.",
        "Operations",
    ),
    (
        "Prior Electricity Sales",
        PRIOR_VALUE.format(metric="Electricity Sales"),
        "0.0 TWh",
        "Immediate prior reported annual sales selected dynamically.",
        "Operations",
    ),
    (
        "Sales YoY %",
        "DIVIDE ( [Latest Electricity Sales] - [Prior Electricity Sales], [Prior Electricity Sales] )",
        "0.0%",
        "Latest sales change against the dynamically selected prior annual observation.",
        "Operations",
    ),
    (
        "Energy Availability Factor",
        'DIVIDE ( CALCULATE ( SUM ( FactMetric[Value] ), FactMetric[Metric] = "Energy Availability Factor" ), 100 )',
        "0.00%",
        "Reported Energy Availability Factor by fiscal year.",
        "Operations",
    ),
    (
        "Latest EAF",
        """VAR LatestPeriod = MAXX ( FILTER ( ALL ( FactMetric ), FactMetric[Metric] = \"Energy Availability Factor\" ), FactMetric[PeriodKey] )
VAR LatestValue = CALCULATE ( MAX ( FactMetric[Value] ), REMOVEFILTERS ( DimPeriod ), FactMetric[Metric] = \"Energy Availability Factor\", FactMetric[PeriodKey] = LatestPeriod )
RETURN DIVIDE ( LatestValue, 100 )""",
        "0.00%",
        "Latest reported EAF selected dynamically.",
        "Operations",
    ),
    (
        "Prior EAF",
        """VAR LatestPeriod = MAXX ( FILTER ( ALL ( FactMetric ), FactMetric[Metric] = \"Energy Availability Factor\" ), FactMetric[PeriodKey] )
VAR PriorPeriod = MAXX ( FILTER ( ALL ( FactMetric ), FactMetric[Metric] = \"Energy Availability Factor\" && FactMetric[PeriodKey] < LatestPeriod ), FactMetric[PeriodKey] )
VAR PriorValue = CALCULATE ( MAX ( FactMetric[Value] ), REMOVEFILTERS ( DimPeriod ), FactMetric[Metric] = \"Energy Availability Factor\", FactMetric[PeriodKey] = PriorPeriod )
RETURN DIVIDE ( PriorValue, 100 )""",
        "0.00%",
        "Immediate prior reported EAF selected dynamically.",
        "Operations",
    ),
    (
        "EAF Change pp",
        "100 * ( [Latest EAF] - [Prior EAF] )",
        "0.00 pp",
        "Percentage-point change against the dynamically selected prior observation.",
        "Operations",
    ),
    (
        "Net Profit After Tax",
        'CALCULATE ( MAX ( FactMetric[Value] ), FactMetric[Metric] = "Net Profit After Tax" )',
        "R0.0,,,bn",
        "Latest reported net profit after tax.",
        "Financial",
    ),
    (
        "Electricity Revenue",
        'CALCULATE ( MAX ( FactMetric[Value] ), FactMetric[Metric] = "Electricity Revenue" )',
        "R0.0,,,bn",
        "Latest governed electricity revenue observation.",
        "Financial",
    ),
    (
        "Security Losses",
        'CALCULATE ( MAX ( FactMetric[Value] ), FactMetric[Metric] = "Estimated Financial Loss" )',
        "R0.0,,m",
        "Aggregate physical-security losses, not coal-specific.",
        "Security",
    ),
    (
        "Security Recoveries",
        'CALCULATE ( MAX ( FactMetric[Value] ), FactMetric[Metric] = "Recoveries" )',
        "R0.0,,m",
        "Aggregate physical-security recoveries, not coal-specific.",
        "Security",
    ),
    (
        "Security Recovery Rate",
        "DIVIDE ( [Security Recoveries], [Security Losses] )",
        "0.0%",
        "Recoveries divided by estimated losses; descriptive, not causal.",
        "Security",
    ),
    (
        "Arrests",
        'CALCULATE ( MAX ( FactMetric[Value] ), FactMetric[Metric] = "Arrests" )',
        "#,0",
        "Aggregate arrests in the physical-security disclosure.",
        "Security",
    ),
    (
        "Convictions",
        'CALCULATE ( MAX ( FactMetric[Value] ), FactMetric[Metric] = "Convictions" )',
        "#,0",
        "Aggregate convictions in the physical-security disclosure.",
        "Security",
    ),
    (
        "Security Metric Value",
        'CALCULATE ( SUM ( FactMetric[Value] ), FactMetric[Domain] = "Security" )',
        "#,0.00",
        "Security-only value used with the metric category; units remain visible in the evidence table.",
        "Security",
    ),
    (
        "Tariff Increase %",
        "DIVIDE ( MAX ( FactTariff[IncreasePct] ), 100 )",
        "0.00%",
        "Average increase for the tariff row in filter context.",
        "Tariff",
    ),
    (
        "FY2026/27 Direct Increase",
        'DIVIDE ( MAXX ( TOPN ( 1, FILTER ( ALL ( FactTariff ), FactTariff[CustomerGroup] = "Direct customers - average" ), FactTariff[EffectiveDate], DESC ), FactTariff[IncreasePct] ), 100 )',
        "0.00%",
        "Latest implemented average direct-customer increase selected dynamically.",
        "Tariff",
    ),
    (
        "FY2026/27 Municipal Increase",
        'DIVIDE ( MAXX ( TOPN ( 1, FILTER ( ALL ( FactTariff ), FactTariff[CustomerGroup] = "Municipal bulk purchases" ), FactTariff[EffectiveDate], DESC ), FactTariff[IncreasePct] ), 100 )',
        "0.00%",
        "Latest implemented average municipal bulk increase selected dynamically.",
        "Tariff",
    ),
    (
        "FY2027/28 Average Increase",
        'DIVIDE ( MAXX ( TOPN ( 1, FILTER ( ALL ( FactTariff ), FactTariff[CustomerGroup] = "Average price path" ), FactTariff[EffectiveDate], DESC ), FactTariff[IncreasePct] ), 100 )',
        "0.00%",
        "Latest average price/revenue path; detailed ERTSA structure is a separate regulatory status.",
        "Tariff",
    ),
    (
        "Illustrative Tariff Index",
        'VAR TariffRows = FILTER ( ALL ( FactTariff ), FactTariff[CustomerGroup] IN { "Direct customers - average", "Average price path" } ) RETURN 100 * PRODUCTX ( TariffRows, 1 + DIVIDE ( FactTariff[IncreasePct], 100 ) )',
        "0.0",
        "Dynamic index of published direct-customer/average paths, baseline 100; not a customer bill forecast.",
        "Tariff",
    ),
    (
        "Tariff Consultation Status",
        'MAXX ( TOPN ( 1, FILTER ( ALL ( FactTariff ), FactTariff[CustomerGroup] = "Average price path" ), FactTariff[EffectiveDate], DESC ), FactTariff[RegulatoryStatus] )',
        "General",
        "Latest regulatory status from the governed tariff table.",
        "Tariff",
    ),
    (
        "Governed Source Count",
        "COUNTROWS ( SourceRegister )",
        "#,0",
        "Number of governed source-register records embedded in the model.",
        "Governance",
    ),
    (
        "Primary Source Count",
        "CALCULATE ( COUNTROWS ( SourceRegister ), SourceRegister[IsPrimary] = TRUE () )",
        "#,0",
        "Direct official or primary-document source records (tier A1/A2).",
        "Governance",
    ),
    (
        "Latest Evidence Date",
        'VAR LatestDate = CALCULATE ( MAX ( SourceRegister[PublicationDate] ), FILTER ( ALL ( SourceRegister ), LEFT ( SourceRegister[EvidenceType], 8 ) <> "SCENARIO" && NOT CONTAINSSTRING ( SourceRegister[VerificationStatus], "Superseded" ) ) ) RETURN FORMAT ( LatestDate, "dd mmm yyyy" )',
        "General",
        "Latest non-scenario, non-superseded evidence date selected from the source register.",
        "Governance",
    ),
]


def query_rows(connection: sqlite3.Connection, view_name: str) -> list[tuple[object, ...]]:
    """Read an allow-listed canonical semantic export view in stable order."""
    order_by = {
        "vw_powerbi_period": "PeriodKey",
        "vw_powerbi_metric": "PeriodKey, Domain, Metric, SourceDatasetId",
        "vw_powerbi_tariff": "PeriodKey, CustomerGroup",
        "vw_powerbi_scenario": "PeriodKey, ScenarioName",
        "vw_powerbi_source": "DatasetId",
    }
    if view_name not in order_by:
        raise ValueError(f"Unsupported semantic export view: {view_name}")
    return [
        tuple(row)
        for row in connection.execute(f"SELECT * FROM {view_name} ORDER BY {order_by[view_name]}")
    ]


def create_semantic_model(connection: sqlite3.Connection) -> int:
    # Recreate generator-owned folders so Desktop migrations cannot leave stale
    # local-date tables or role layouts in the source-controlled model.
    model_root = MODEL_DEF.resolve()
    for generated_dir in (MODEL_DEF / "tables", MODEL_DEF / "roles"):
        resolved_dir = generated_dir.resolve()
        if model_root not in resolved_dir.parents:
            raise RuntimeError(f"Refusing to clean path outside semantic model: {resolved_dir}")
        shutil.rmtree(resolved_dir, ignore_errors=True)
        resolved_dir.mkdir(parents=True, exist_ok=True)
    (MODEL_DEF / "roles.tmdl").unlink(missing_ok=True)
    tables: dict[
        str, tuple[list[tuple[str, str]], list[tuple[object, ...]], set[str], set[str]]
    ] = {
        "DimPeriod": (
            [
                ("PeriodKey", "int64"),
                ("FiscalYear", "string"),
                ("EffectiveDate", "dateTime"),
                ("PeriodLabel", "string"),
                ("SortOrder", "int64"),
                ("IsFiscalYearEnd", "boolean"),
                ("IsScenarioHorizon", "boolean"),
            ],
            query_rows(connection, "vw_powerbi_period"),
            {"PeriodKey"},
            {"PeriodKey", "SortOrder", "IsScenarioHorizon"},
        ),
        "FactMetric": (
            [
                ("PeriodKey", "int64"),
                ("Domain", "string"),
                ("Metric", "string"),
                ("Value", "double"),
                ("Unit", "string"),
                ("EvidenceType", "string"),
                ("SourceDatasetId", "string"),
            ],
            query_rows(connection, "vw_powerbi_metric"),
            set(),
            {"PeriodKey"},
        ),
        "FactTariff": (
            [
                ("PeriodKey", "int64"),
                ("FiscalYear", "string"),
                ("CustomerGroup", "string"),
                ("IncreasePct", "double"),
                ("EffectiveDate", "dateTime"),
                ("RegulatoryStatus", "string"),
                ("SourceDatasetId", "string"),
                ("StatusSourceDatasetId", "string"),
            ],
            query_rows(connection, "vw_powerbi_tariff"),
            set(),
            {"PeriodKey"},
        ),
        "FactScenario": (
            [
                ("PeriodKey", "int64"),
                ("ScenarioName", "string"),
                ("Metric", "string"),
                ("Value", "double"),
                ("Unit", "string"),
                ("EvidenceType", "string"),
                ("SourceDatasetId", "string"),
            ],
            query_rows(connection, "vw_powerbi_scenario"),
            set(),
            {"PeriodKey"},
        ),
        "SourceRegister": (
            [
                ("DatasetId", "string"),
                ("Metric", "string"),
                ("Publisher", "string"),
                ("SourceTier", "string"),
                ("PublicationDate", "dateTime"),
                ("EvidenceType", "string"),
                ("VerificationStatus", "string"),
                ("SourceUrl", "string"),
                ("IsPrimary", "boolean"),
            ],
            query_rows(connection, "vw_powerbi_source"),
            {"DatasetId"},
            set(),
        ),
    }

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
        f"annotation PBI_QueryOrder = {json.dumps(model_tables, separators=(',', ':'))}",
        "",
        "annotation __PBI_TimeIntelligenceEnabled = 0",
        "",
        'annotation PBI_ProTooling = ["DevMode"]',
        "",
        *[f"ref table {quote_name(table)}" for table in model_tables],
        "",
        "ref role Viewer",
        "",
    ]
    write(MODEL_DEF / "model.tmdl", "\n".join(model))
    write(MODEL_DEF / "database.tmdl", "database\n\tcompatibilityLevel: 1606\n")

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
        MODEL_DEF / "roles" / "Viewer.tmdl",
        """
        role Viewer
            modelPermission: read
        """,
    )
    write(
        ROOT / "powerbi" / "dax" / "measures.dax",
        "-- GENERATED by scripts/build_powerbi_project.py; edit MEASURES there.\n\n"
        + "\n\n".join(
            f"-- {description}\n{name} =\n{expression}"
            for name, expression, _, description, _ in MEASURES
        )
        + "\n",
    )
    return len(tables["SourceRegister"][1])


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
        "objects": {
            "general": [{"properties": {"paragraphs": [{"textRuns": [{"value": value}]}]}}]
        },
    }
    return result


def card(
    name: str, title: str, measure: str, x: int, y: int, width: int, height: int, z: int
) -> dict:
    result = visual_base(name, x, y, width, height, z)
    result["visual"] = {
        "visualType": "card",
        "query": {"queryState": {"Values": {"projections": [measure_field(measure)]}}},
        "visualContainerObjects": title_config(title),
    }
    return result


def slicer(
    name: str, title: str, field: tuple[str, str], x: int, y: int, width: int, height: int, z: int
) -> dict:
    result = visual_base(name, x, y, width, height, z)
    result["visual"] = {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [column_field(*field)]}}},
        "visualContainerObjects": title_config(title),
    }
    return result


def chart(
    name: str,
    visual_type: str,
    title: str,
    category: tuple[str, str],
    measure: str,
    x: int,
    y: int,
    width: int,
    height: int,
    z: int,
    series: tuple[str, str] | None = None,
) -> dict:
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


def table_visual(
    name: str,
    title: str,
    fields: list[tuple[str, str]],
    x: int,
    y: int,
    width: int,
    height: int,
    z: int,
) -> dict:
    result = visual_base(name, x, y, width, height, z)
    result["visual"] = {
        "visualType": "tableEx",
        "query": {
            "queryState": {"Values": {"projections": [column_field(*field) for field in fields]}}
        },
        "visualContainerObjects": title_config(title),
    }
    return result


PAGES = [
    {
        "name": "Executive Overview",
        "slug": "executive-overview",
        "slicer": ("Fiscal period", ("DimPeriod", "FiscalYear")),
        "kpis": [
            "Latest Year-End Municipal Arrears",
            "Latest Electricity Sales",
            "Latest EAF",
            "Net Profit After Tax",
            "FY2027/28 Average Increase",
            "Governed Source Count",
        ],
        "charts": [
            (
                "lineChart",
                "Municipal arrears at fiscal year-end",
                ("DimPeriod", "FiscalYear"),
                "Year-End Municipal Arrears",
                None,
            ),
            (
                "lineChart",
                "Electricity sales trend",
                ("DimPeriod", "FiscalYear"),
                "Electricity Sales",
                None,
            ),
            (
                "lineChart",
                "Energy Availability Factor",
                ("DimPeriod", "FiscalYear"),
                "Energy Availability Factor",
                None,
            ),
            (
                "clusteredColumnChart",
                "Tariff path by customer group",
                ("FactTariff", "FiscalYear"),
                "Tariff Increase %",
                ("FactTariff", "CustomerGroup"),
            ),
        ],
    },
    {
        "name": "Tariff & Affordability",
        "slug": "tariff-affordability",
        "slicer": ("Customer group", ("FactTariff", "CustomerGroup")),
        "kpis": [
            "FY2026/27 Direct Increase",
            "FY2026/27 Municipal Increase",
            "FY2027/28 Average Increase",
            "Illustrative Tariff Index",
            "Latest Electricity Sales",
            "Electricity Revenue",
        ],
        "charts": [
            (
                "lineChart",
                "Average tariff path",
                ("FactTariff", "FiscalYear"),
                "Tariff Increase %",
                ("FactTariff", "CustomerGroup"),
            ),
            (
                "clusteredColumnChart",
                "Sales alongside tariff cycles",
                ("DimPeriod", "FiscalYear"),
                "Electricity Sales",
                None,
            ),
        ],
        "table": (
            "Regulatory status and lineage",
            [
                ("FactTariff", "FiscalYear"),
                ("FactTariff", "CustomerGroup"),
                ("FactTariff", "IncreasePct"),
                ("FactTariff", "EffectiveDate"),
                ("FactTariff", "RegulatoryStatus"),
                ("FactTariff", "SourceDatasetId"),
            ],
        ),
    },
    {
        "name": "Municipal Debt",
        "slug": "municipal-debt",
        "slicer": ("Fiscal period", ("DimPeriod", "FiscalYear")),
        "kpis": [
            "Latest Year-End Municipal Arrears",
            "Latest In-Year Municipal Arrears",
            "Municipal Arrears YoY %",
            "Scenario Municipal Arrears FY2031",
            "Scenario Gap vs Latest",
            "Governed Source Count",
        ],
        "charts": [
            (
                "lineChart",
                "Reported fiscal-year-end arrears",
                ("DimPeriod", "FiscalYear"),
                "Year-End Municipal Arrears",
                None,
            ),
            (
                "clusteredColumnChart",
                "Reported vs management scenario",
                ("DimPeriod", "FiscalYear"),
                "Scenario Municipal Arrears FY2031",
                None,
            ),
        ],
        "table": (
            "Governed metric observations",
            [
                ("FactMetric", "Domain"),
                ("FactMetric", "Metric"),
                ("FactMetric", "Value"),
                ("FactMetric", "Unit"),
                ("FactMetric", "EvidenceType"),
                ("FactMetric", "SourceDatasetId"),
            ],
        ),
    },
    {
        "name": "Operations & Security",
        "slug": "operations-security",
        "slicer": ("Metric domain", ("FactMetric", "Domain")),
        "kpis": [
            "Latest Electricity Sales",
            "Sales YoY %",
            "Latest EAF",
            "EAF Change pp",
            "Security Losses",
            "Security Recovery Rate",
        ],
        "charts": [
            (
                "lineChart",
                "Electricity sales",
                ("DimPeriod", "FiscalYear"),
                "Electricity Sales",
                None,
            ),
            (
                "lineChart",
                "Energy availability",
                ("DimPeriod", "FiscalYear"),
                "Energy Availability Factor",
                None,
            ),
            (
                "clusteredColumnChart",
                "Aggregate security metrics",
                ("FactMetric", "Metric"),
                "Security Metric Value",
                None,
            ),
        ],
        "table": (
            "Governed metric evidence — security rows are domain-labelled",
            [
                ("FactMetric", "Domain"),
                ("FactMetric", "Metric"),
                ("FactMetric", "Value"),
                ("FactMetric", "Unit"),
                ("FactMetric", "SourceDatasetId"),
            ],
        ),
    },
    {
        "name": "Data Governance",
        "slug": "data-governance",
        "slicer": ("Source tier", ("SourceRegister", "SourceTier")),
        "kpis": [
            "Governed Source Count",
            "Primary Source Count",
            "Latest Evidence Date",
            "FY2027/28 Average Increase",
            "Latest Year-End Municipal Arrears",
            "Latest EAF",
        ],
        "charts": [
            (
                "donutChart",
                "Sources by evidence type",
                ("SourceRegister", "EvidenceType"),
                "Governed Source Count",
                None,
            ),
            (
                "clusteredBarChart",
                "Sources by tier",
                ("SourceRegister", "SourceTier"),
                "Governed Source Count",
                None,
            ),
        ],
        "table": (
            "Evidence register",
            [
                ("SourceRegister", "DatasetId"),
                ("SourceRegister", "Metric"),
                ("SourceRegister", "Publisher"),
                ("SourceRegister", "SourceTier"),
                ("SourceRegister", "PublicationDate"),
                ("SourceRegister", "VerificationStatus"),
            ],
        ),
    },
]


def create_report(connection: sqlite3.Connection) -> tuple[int, int]:
    page_order: list[str] = []
    visual_count = 0
    nav = "EXECUTIVE  |  TARIFF & AFFORDABILITY  |  MUNICIPAL DEBT  |  OPERATIONS & SECURITY  |  DATA GOVERNANCE"
    freshness = connection.execute(
        "SELECT data_reported_as_of FROM vw_report_freshness"
    ).fetchone()[0]
    freshness_label = date.fromisoformat(freshness).strftime("%d %b %Y").upper()
    tariff_path = connection.execute("""
        SELECT IncreasePct FROM vw_powerbi_tariff
        WHERE CustomerGroup = 'Average price path'
        ORDER BY EffectiveDate DESC LIMIT 1
    """).fetchone()[0]
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
        visuals.append(
            textbox(
                stable_id(f"{page_id}-title"),
                f"ESKOM STRATEGIC INTELLIGENCE  |  {page['name']}",
                20,
                12,
                1240,
                38,
                z,
            )
        )
        z += 1
        visuals.append(textbox(stable_id(f"{page_id}-nav"), nav, 20, 54, 990, 28, z))
        z += 1
        slicer_title, slicer_field = page["slicer"]
        visuals.append(
            slicer(stable_id(f"{page_id}-slicer"), slicer_title, slicer_field, 1020, 50, 240, 40, z)
        )
        z += 1
        for index, metric in enumerate(page["kpis"]):
            visuals.append(
                card(
                    stable_id(f"{page_id}-kpi-{index}"),
                    metric,
                    metric,
                    20 + index * 205,
                    94,
                    190,
                    118,
                    z,
                )
            )
            z += 1
        charts = page["charts"]
        chart_columns = 2 if len(charts) in {2, 4} else 3
        chart_width = 600 if chart_columns == 2 else 395
        chart_height = 165 if len(charts) == 4 else 195
        chart_x_step = 620 if chart_columns == 2 else 415
        chart_y_step = 180 if len(charts) == 4 else 210
        for index, (visual_type, title, category, metric, series) in enumerate(charts):
            x = 20 + (index % chart_columns) * chart_x_step
            y = 232 + (index // chart_columns) * chart_y_step
            visuals.append(
                chart(
                    stable_id(f"{page_id}-chart-{index}"),
                    visual_type,
                    title,
                    category,
                    metric,
                    x,
                    y,
                    chart_width,
                    chart_height,
                    z,
                    series,
                )
            )
            z += 1
        if "table" in page:
            table_title, fields = page["table"]
            visuals.append(
                table_visual(
                    stable_id(f"{page_id}-table"), table_title, fields, 20, 445, 1240, 210, z
                )
            )
            z += 1
        elif len(charts) >= 3:
            insight_y = 592 if len(charts) == 4 else 452
            insight_height = 60 if len(charts) == 4 else 72
            visuals.append(
                textbox(
                    stable_id(f"{page_id}-insight"),
                    "Decision lens: separate reported actuals, derived indicators and management scenarios before interpreting the trend.",
                    20,
                    insight_y,
                    1240,
                    insight_height,
                    z,
                )
            )
            z += 1
        disclosure = f"PUBLIC-DATA PORTFOLIO PROJECT  •  NO CUSTOMER OR OPERATIONAL DATA  •  EVIDENCE CURRENT TO {freshness_label}  •  RUNTIME STATUS IN docs/POWER_BI_RUNBOOK.md"
        if page["slug"] == "tariff-affordability":
            disclosure = f"{tariff_path:.2f}% = FY2027/28 AVERAGE PATH  •  ERTSA STRUCTURE/CUSTOMER ALLOCATION UNDER NERSA CONSULTATION AT {freshness_label}  •  INDEX IS NOT A BILL FORECAST"
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
        {
            "$schema": f"{SCHEMA_ROOT}/report/definition/versionMetadata/1.0.0/schema.json",
            "version": "2.0.0",
        },
    )
    theme_name = "EskomStrategicIntelligenceTheme"
    write_json(
        REPORT_DEF / "report.json",
        {
            "$schema": f"{SCHEMA_ROOT}/report/definition/report/3.2.0/schema.json",
            "themeCollection": {
                "customTheme": {
                    "name": theme_name,
                    "reportVersionAtImport": {
                        "visual": "2.9.0",
                        "report": "3.2.0",
                        "page": "2.1.0",
                    },
                    "type": "RegisteredResources",
                }
            },
            "filterConfig": {"filters": []},
            "resourcePackages": [
                {
                    "name": "RegisteredResources",
                    "type": "RegisteredResources",
                    "items": [
                        {
                            "name": theme_name,
                            "path": "eskom-intelligence-theme.json",
                            "type": "CustomTheme",
                        }
                    ],
                }
            ],
            "settings": {
                "useStylableVisualContainerHeader": True,
                "defaultFilterActionIsDataFilter": True,
                "defaultDrillFilterOtherVisuals": True,
                "allowChangeFilterTypes": True,
                "allowInlineExploration": True,
                "useEnhancedTooltips": True,
                "useDefaultAggregateDisplayName": True,
            },
            "slowDataSourceSettings": {
                "isCrossHighlightingDisabled": False,
                "isSlicerSelectionsButtonEnabled": False,
                "isFilterSelectionsButtonEnabled": False,
                "isFieldWellButtonEnabled": False,
                "isApplyAllButtonEnabled": False,
            },
        },
    )
    theme = {
        "name": "Eskom Strategic Intelligence",
        "dataColors": [
            COLORS["teal"],
            COLORS["blue"],
            COLORS["gold"],
            COLORS["coral"],
            "#7FB069",
            "#8E7DBE",
        ],
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
        "visualStyles": {
            "*": {
                "*": {
                    "background": [
                        {"color": {"solid": {"color": COLORS["panel"]}}, "transparency": 2}
                    ],
                    "border": [
                        {"show": True, "color": {"solid": {"color": COLORS["line"]}}, "radius": 8}
                    ],
                    "title": [
                        {
                            "show": True,
                            "fontFace": "Segoe UI Semibold",
                            "fontSize": 11,
                            "fontColor": {"solid": {"color": COLORS["white"]}},
                        }
                    ],
                    "visualHeader": [
                        {"show": True, "foreground": {"solid": {"color": COLORS["muted"]}}}
                    ],
                }
            },
            "page": {
                "*": {
                    "background": [
                        {"color": {"solid": {"color": COLORS["ink"]}}, "transparency": 0}
                    ]
                }
            },
        },
    }
    write_json(
        REPORT / "StaticResources" / "RegisteredResources" / "eskom-intelligence-theme.json", theme
    )


def create_preview(connection: sqlite3.Connection) -> None:
    annual = connection.execute("""
        SELECT d.fiscal_year_label, f.gross_arrears_rand / 1000000000.0
        FROM fact_municipal_debt f
        JOIN dim_date d USING (date_key)
        WHERE f.municipality_key = 0 AND d.is_fiscal_year_end = TRUE
        ORDER BY d.fiscal_year
    """).fetchall()
    values = [row[1] for row in annual]
    bars = []
    for index, (label, value) in enumerate(annual):
        height = value / max(values) * 170
        x = 680 + index * 45
        y = 540 - height
        value_label = (
            f'<text x="{x + 16}" y="{y - 8:.0f}" text-anchor="middle" class="tiny">{value:.1f}</text>'
            if index in {0, len(annual) - 3, len(annual) - 2, len(annual) - 1}
            else ""
        )
        bars.append(
            f'<rect x="{x}" y="{y:.0f}" width="32" height="{height:.0f}" rx="4" fill="{COLORS["teal"]}"/>{value_label}<text x="{x + 16}" y="570" text-anchor="middle" class="tiny">{label[2:]}</text>'
        )
    metrics = dict(
        connection.execute("""
        SELECT Metric, Value FROM vw_powerbi_metric
        WHERE PeriodKey = (SELECT MAX(PeriodKey) FROM vw_powerbi_metric m2 WHERE m2.Metric = vw_powerbi_metric.Metric)
    """).fetchall()
    )
    source_count = connection.execute("SELECT COUNT(*) FROM vw_powerbi_source").fetchone()[0]
    tariff_path = connection.execute("""
        SELECT IncreasePct FROM vw_powerbi_tariff
        WHERE CustomerGroup = 'Average price path'
        ORDER BY EffectiveDate DESC LIMIT 1
    """).fetchone()[0]
    freshness = connection.execute(
        "SELECT data_reported_as_of FROM vw_report_freshness"
    ).fetchone()[0]
    freshness_label = date.fromisoformat(freshness).strftime("%d %B %Y")
    kpis = [
        ("YEAR-END ARREARS", f"R{metrics['Municipal Arrears - Year End'] / 1e9:.1f}bn"),
        ("ELECTRICITY SALES", f"{metrics['Electricity Sales']:.0f} TWh"),
        ("EAF", f"{metrics['Energy Availability Factor']:.2f}%"),
        ("NET PROFIT", f"R{metrics['Net Profit After Tax'] / 1e9:.1f}bn"),
        ("FY2027/28 PATH", f"{tariff_path:.2f}%"),
        ("GOVERNED SOURCES", str(source_count)),
    ]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
    <style>.title{{font:700 28px 'Segoe UI';fill:{COLORS["white"]}}}.sub{{font:14px 'Segoe UI';fill:{COLORS["muted"]}}}.k{{font:600 13px 'Segoe UI';fill:{COLORS["muted"]}}}.v{{font:700 26px 'Segoe UI';fill:{COLORS["white"]}}}.small{{font:600 13px 'Segoe UI';fill:{COLORS["white"]}}}.muted{{font:12px 'Segoe UI';fill:{COLORS["muted"]}}}.tiny{{font:600 9px 'Segoe UI';fill:{COLORS["white"]}}}</style>
    <rect width="1280" height="720" fill="{COLORS["ink"]}"/><text x="42" y="58" class="title">ESKOM STRATEGIC INTELLIGENCE</text><text x="42" y="86" class="sub">Power BI Project preview • governed public evidence • latest evidence {freshness_label}</text>
    <rect x="42" y="112" width="1196" height="2" fill="{COLORS["teal"]}"/>
    <g>{"".join(f'<rect x="{42 + i * 196}" y="142" width="180" height="112" rx="10" fill="{COLORS["panel"]}" stroke="{COLORS["line"]}"/><text x="{58 + i * 196}" y="174" class="k">{label}</text><text x="{58 + i * 196}" y="218" class="v">{value}</text>' for i, (label, value) in enumerate(kpis))}</g>
    <rect x="42" y="286" width="590" height="320" rx="12" fill="{COLORS["panel"]}" stroke="{COLORS["line"]}"/><text x="66" y="322" class="small">TARIFF PATH &amp; REGULATORY STATUS</text>
    <text x="66" y="378" class="v" fill="{COLORS["gold"]}">{tariff_path:.2f}%</text><text x="66" y="408" class="small">FY2027/28 average price/revenue path</text><text x="66" y="446" class="sub">Intended effective date: 01 April 2027</text><text x="66" y="476" class="sub">Detailed ERTSA structure and customer-category allocation</text><text x="66" y="502" class="sub">under NERSA consultation; path is not a final category tariff.</text><rect x="66" y="536" width="230" height="36" rx="18" fill="{COLORS["gold"]}"/><text x="181" y="560" text-anchor="middle" style="font:700 13px 'Segoe UI';fill:{COLORS["ink"]}">STATUS: CONSULTATION</text>
    <rect x="654" y="286" width="584" height="320" rx="12" fill="{COLORS["panel"]}" stroke="{COLORS["line"]}"/><text x="678" y="322" class="small">MUNICIPAL ARREARS • FY2015–FY2026 • R BILLION</text>{"".join(bars)}
    <text x="42" y="660" class="muted">Source-controlled PBIP • PBIR report • TMDL semantic model • automated QA • no private operational data</text><text x="42" y="684" class="muted">Preview only: interactive rendering requires Power BI Desktop or publication to Power BI Service.</text></svg>'''
    write(ROOT / "assets" / "eskom-power-bi-preview.svg", svg)


def main(connection: sqlite3.Connection | None = None) -> dict[str, int]:
    owns_connection = connection is None
    if connection is None:
        from src.analytics.build_database import build_database
        from src.validation.quality import run_quality_checks

        connection, _ = build_database()
        failures = [result.name for result in run_quality_checks(connection) if not result.passed]
        if failures:
            connection.close()
            raise RuntimeError(f"Power BI generation blocked by QA failures: {failures}")
    try:
        create_foundation()
        source_count = create_semantic_model(connection)
        pages, visuals = create_report(connection)
        create_preview(connection)
        summary = {
            "pages": pages,
            "visuals": visuals,
            "measures": len(MEASURES),
            "sources": source_count,
        }
        print(
            f"PASS: Power BI Project generated from validated SQLite ({pages} pages, {visuals} visuals, {len(MEASURES)} measures, {source_count} sources)"
        )
        return summary
    finally:
        if owns_connection:
            connection.close()


if __name__ == "__main__":
    main()
