"""Structural release tests for the text-based Power BI Project."""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = "EskomStrategicIntelligence"
MEASURE_TABLE = "MeasureCatalog"
REPORT = ROOT / f"{PROJECT}.Report"
MODEL = ROOT / f"{PROJECT}.SemanticModel"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_pbip_links_report_and_semantic_model():
    pbip = load_json(ROOT / f"{PROJECT}.pbip")
    pbir = load_json(REPORT / "definition.pbir")
    assert pbip["artifacts"] == [{"report": {"path": f"{PROJECT}.Report"}}]
    assert pbir["datasetReference"]["byPath"]["path"] == f"../{PROJECT}.SemanticModel"
    assert (MODEL / "definition.pbism").is_file()


def test_all_powerbi_json_is_valid_and_schema_governed():
    json_files = [ROOT / f"{PROJECT}.pbip", *REPORT.rglob("*.json")]
    assert len(json_files) >= 65
    for path in json_files:
        payload = load_json(path)
        if path.name != "eskom-intelligence-theme.json":
            assert payload.get("$schema", "").startswith(
                "https://developer.microsoft.com/json-schemas/fabric/"
            ), path


def test_report_has_five_ordered_pages_and_68_visuals():
    pages_root = REPORT / "definition" / "pages"
    metadata = load_json(pages_root / "pages.json")
    page_ids = metadata["pageOrder"]
    assert len(page_ids) == 5
    assert metadata["activePageName"] == page_ids[0]
    display_names = []
    visual_count = 0
    for page_id in page_ids:
        page = load_json(pages_root / page_id / "page.json")
        display_names.append(page["displayName"])
        visuals = list((pages_root / page_id / "visuals").glob("*/visual.json"))
        assert len(visuals) >= 12
        visual_count += len(visuals)
    assert len(display_names) == len(set(display_names))
    assert visual_count == 68


def test_report_visuals_do_not_overlap_or_leave_the_canvas():
    pages_root = REPORT / "definition" / "pages"
    for page_path in pages_root.glob("*/page.json"):
        page = load_json(page_path)
        visuals = [
            load_json(path)
            for path in (page_path.parent / "visuals").glob("*/visual.json")
        ]
        for visual in visuals:
            position = visual["position"]
            assert position["x"] >= 0 and position["y"] >= 0, visual["name"]
            assert position["x"] + position["width"] <= page["width"], visual["name"]
            assert position["y"] + position["height"] <= page["height"], visual["name"]
        for index, first in enumerate(visuals):
            a = first["position"]
            for second in visuals[index + 1 :]:
                b = second["position"]
                overlap = (
                    a["x"] < b["x"] + b["width"]
                    and b["x"] < a["x"] + a["width"]
                    and a["y"] < b["y"] + b["height"]
                    and b["y"] < a["y"] + a["height"]
                )
                assert not overlap, f"{page['displayName']}: {first['name']} overlaps {second['name']}"


def test_visual_measure_references_exist():
    measures_text = (MODEL / "definition" / "tables" / f"{MEASURE_TABLE}.tmdl").read_text(
        encoding="utf-8"
    )
    measure_names = set(re.findall(r"^\s*measure (?:'([^']+)'|([^=]+?))\s*=", measures_text, re.MULTILINE))
    available = {quoted or plain.strip() for quoted, plain in measure_names}
    referenced = set()
    for path in REPORT.rglob("visual.json"):
        payload = load_json(path)
        for match in re.finditer(r'"Property":\s*"([^"]+)"', json.dumps(payload)):
            value = match.group(1)
            if f"{MEASURE_TABLE}.{value}" in json.dumps(payload):
                referenced.add(value)
    assert referenced <= available, sorted(referenced - available)


def test_semantic_model_is_self_contained_and_has_relationships():
    text = "\n".join(
        path.read_text(encoding="utf-8") for path in (MODEL / "definition").rglob("*.tmdl")
    )
    for table in [
        "DimPeriod",
        "FactMetric",
        "FactTariff",
        "FactScenario",
        "SourceRegister",
        MEASURE_TABLE,
    ]:
        assert f"ref table {table}" in text or f"ref table '{table}'" in text
    assert text.count("relationship ") == 3
    assert "#table(" in text
    assert not (MODEL / "definition" / "tables" / "Measures.tmdl").exists()
    assert "ref table Measures" not in text
    local_path_pattern = r"[A-Za-z]:\\Us" + r"ers\\|/Us" + r"ers/|/ho" + r"me/"
    assert not re.search(local_path_pattern, text, re.IGNORECASE)
    assert "File.Contents" not in text


def test_inline_power_query_table_types_use_valid_m_tokens():
    table_files = (MODEL / "definition" / "tables").glob("*.tmdl")
    table_type_lines = [
        line
        for path in table_files
        for line in path.read_text(encoding="utf-8").splitlines()
        if "type table [" in line
    ]
    assert len(table_type_lines) == 6
    for line in table_type_lines:
        assert not re.search(r"=\s+type\s+(?:text|number|date|logical)\b", line), line


def test_883_status_and_lineage_are_not_overstated():
    tariff = (MODEL / "definition" / "tables" / "FactTariff.tmdl").read_text(encoding="utf-8")
    measures = (MODEL / "definition" / "tables" / f"{MEASURE_TABLE}.tmdl").read_text(
        encoding="utf-8"
    )
    assert "8.83" in tariff
    assert "under NERSA consultation" in tariff
    assert "DS035" in tariff and "DS037" in tariff
    assert "not a customer bill forecast" in measures
    assert "fully final" not in tariff.lower()


def test_preview_is_explicitly_not_a_runtime_screenshot():
    preview = (ROOT / "assets" / "eskom-power-bi-preview.svg").read_text(encoding="utf-8")
    ET.fromstring(preview)
    assert "Preview only" in preview
    assert "interactive rendering requires Power BI Desktop" in preview
    assert not list(ROOT.glob("*.pbix")), "No generated or fake PBIX binary may be committed"
