import pytest

from satview.config import load_config


def write_yaml(tmp_path, text):
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    return str(path)


VALID_MINIMAL = """
sites:
  - name: Home
    latitude: 40.758
    longitude: -73.9855
satellites:
  - norad_id: 25544
"""


def test_valid_minimal_config_applies_defaults(tmp_path):
    config = load_config(write_yaml(tmp_path, VALID_MINIMAL))

    assert config["sites"][0]["elevation_m"] == 0.0
    assert config["search"]["start"] == "now"
    assert config["search"]["hours"] == 48
    assert config["elevation_mask_deg"] == 0.0
    assert config["output"] is None


def test_missing_file_raises_clear_error(tmp_path):
    with pytest.raises(ValueError, match="not found"):
        load_config(str(tmp_path / "does_not_exist.yaml"))


def test_malformed_yaml_raises_clear_error(tmp_path):
    with pytest.raises(ValueError, match="not valid YAML"):
        load_config(write_yaml(tmp_path, "not: valid: yaml: ["))


def test_empty_file_raises(tmp_path):
    with pytest.raises(ValueError, match="empty or invalid"):
        load_config(write_yaml(tmp_path, ""))


def test_missing_sites_raises(tmp_path):
    text = "satellites:\n  - norad_id: 25544\n"
    with pytest.raises(ValueError, match="sites"):
        load_config(write_yaml(tmp_path, text))


def test_missing_satellites_raises(tmp_path):
    text = "sites:\n  - name: Home\n    latitude: 1\n    longitude: 1\n"
    with pytest.raises(ValueError, match="satellites"):
        load_config(write_yaml(tmp_path, text))


def test_site_missing_required_field_raises(tmp_path):
    text = "sites:\n  - name: Home\n    latitude: 1\nsatellites:\n  - norad_id: 1\n"
    with pytest.raises(ValueError, match="longitude"):
        load_config(write_yaml(tmp_path, text))


@pytest.mark.parametrize("latitude", [90.1, -90.1, 400])
def test_out_of_range_latitude_raises(tmp_path, latitude):
    text = f"sites:\n  - name: Home\n    latitude: {latitude}\n    longitude: 1\nsatellites:\n  - norad_id: 1\n"
    with pytest.raises(ValueError, match="latitude"):
        load_config(write_yaml(tmp_path, text))


@pytest.mark.parametrize("longitude", [180.1, -180.1, 999])
def test_out_of_range_longitude_raises(tmp_path, longitude):
    text = f"sites:\n  - name: Home\n    latitude: 1\n    longitude: {longitude}\nsatellites:\n  - norad_id: 1\n"
    with pytest.raises(ValueError, match="longitude"):
        load_config(write_yaml(tmp_path, text))


def test_satellite_missing_norad_id_raises(tmp_path):
    text = "sites:\n  - name: Home\n    latitude: 1\n    longitude: 1\nsatellites:\n  - name: Foo\n"
    with pytest.raises(ValueError, match="norad_id"):
        load_config(write_yaml(tmp_path, text))


@pytest.mark.parametrize("norad_id", [-1, 0, "abc"])
def test_invalid_norad_id_raises(tmp_path, norad_id):
    text = (
        "sites:\n  - name: Home\n    latitude: 1\n    longitude: 1\n"
        f"satellites:\n  - norad_id: {norad_id!r}\n"
    )
    with pytest.raises(ValueError, match="norad_id"):
        load_config(write_yaml(tmp_path, text))


@pytest.mark.parametrize("hours", [0, -5])
def test_non_positive_search_hours_raises(tmp_path, hours):
    text = VALID_MINIMAL + f"search:\n  hours: {hours}\n"
    with pytest.raises(ValueError, match="hours"):
        load_config(write_yaml(tmp_path, text))


def test_output_section_requires_path(tmp_path):
    text = VALID_MINIMAL + "output:\n  format: csv\n"
    with pytest.raises(ValueError, match="path"):
        load_config(write_yaml(tmp_path, text))


def test_output_format_defaults_to_none_for_inference(tmp_path):
    text = VALID_MINIMAL + "output:\n  path: out.csv\n"
    config = load_config(write_yaml(tmp_path, text))
    assert config["output"]["format"] is None


def test_multiple_sites_and_satellites_all_parsed(tmp_path):
    text = """
sites:
  - name: Home
    latitude: 40.758
    longitude: -73.9855
  - name: Denver
    latitude: 39.7392
    longitude: -104.9903
    elevation_m: 1609
satellites:
  - norad_id: 25544
  - norad_id: 20580
"""
    config = load_config(write_yaml(tmp_path, text))
    assert len(config["sites"]) == 2
    assert len(config["satellites"]) == 2
    assert config["sites"][1]["elevation_m"] == 1609
