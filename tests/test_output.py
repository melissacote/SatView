import csv
import json
from zoneinfo import ZoneInfo

import pytest
from skyfield.api import load

from satview.output import build_record, infer_format, write_csv, write_json, write_results

ts = load.timescale()
NY = ZoneInfo("America/New_York")


def make_pass(optically_visible=True, peak_magnitude=-3.9):
    p = {
        "rise_time": ts.utc(2026, 7, 22, 21, 46, 50),
        "rise_el": 0.0,
        "rise_az": 308.0,
        "peak_time": ts.utc(2026, 7, 22, 21, 52, 20),
        "peak_el": 60.4,
        "peak_az": 33.6,
        "set_time": ts.utc(2026, 7, 22, 21, 57, 47),
        "set_el": -0.0,
        "set_az": 118.9,
        "optically_visible": optically_visible,
    }
    if optically_visible:
        p["optical_rise_time"] = p["rise_time"]
        p["optical_set_time"] = ts.utc(2026, 7, 22, 21, 53, 49)
        p["peak_magnitude"] = peak_magnitude
    return p


def test_build_record_visible_pass_has_expected_fields():
    record = build_record("Home", "ISS (ZARYA)", 25544, NY, make_pass())

    assert record["site"] == "Home"
    assert record["satellite_name"] == "ISS (ZARYA)"
    assert record["norad_id"] == 25544
    assert record["peak_el_deg"] == 60.4
    assert record["optically_visible"] is True
    assert record["optical_rise_time_local"] is not None
    assert record["peak_magnitude"] == -3.9
    assert record["rise_time_local"].startswith("2026-07-22T17:46:50")  # EDT = UTC-4


def test_build_record_non_visible_pass_has_null_optical_fields():
    record = build_record("Home", "ISS (ZARYA)", 25544, NY, make_pass(optically_visible=False))

    assert record["optically_visible"] is False
    assert record["optical_rise_time_local"] is None
    assert record["optical_set_time_local"] is None
    assert record["peak_magnitude"] is None


def test_build_record_missing_catalog_magnitude_is_null():
    p = make_pass(peak_magnitude=None)
    record = build_record("Home", "HST", 20580, NY, p)
    assert record["peak_magnitude"] is None


@pytest.mark.parametrize("path,expected", [("out.csv", "csv"), ("out.json", "json"), ("OUT.CSV", "csv")])
def test_infer_format_from_extension(path, expected):
    assert infer_format(path) == expected


def test_infer_format_explicit_overrides_extension():
    assert infer_format("out.csv", explicit_format="json") == "json"


def test_infer_format_unknown_extension_raises():
    with pytest.raises(ValueError, match="Cannot infer"):
        infer_format("out.txt")


def test_write_csv_round_trip(tmp_path):
    record = build_record("Home", "ISS (ZARYA)", 25544, NY, make_pass())
    path = tmp_path / "out.csv"
    write_csv([record], str(path))

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["site"] == "Home"
    assert rows[0]["norad_id"] == "25544"


def test_write_json_round_trip(tmp_path):
    record = build_record("Home", "ISS (ZARYA)", 25544, NY, make_pass())
    path = tmp_path / "out.json"
    write_json([record], str(path))

    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert data == [record]


def test_write_results_dispatches_by_extension(tmp_path):
    record = build_record("Home", "ISS (ZARYA)", 25544, NY, make_pass())
    path = tmp_path / "out.json"
    write_results([record], str(path))

    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert data[0]["norad_id"] == 25544
