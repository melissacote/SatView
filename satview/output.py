import csv
import json
import os

FIELDNAMES = [
    "site",
    "satellite_name",
    "norad_id",
    "rise_time_utc",
    "rise_time_local",
    "rise_el_deg",
    "rise_az_deg",
    "peak_time_utc",
    "peak_time_local",
    "peak_el_deg",
    "peak_az_deg",
    "set_time_utc",
    "set_time_local",
    "set_el_deg",
    "set_az_deg",
    "optically_visible",
    "optical_rise_time_local",
    "optical_set_time_local",
    "peak_magnitude",
]


def build_record(site_name, satellite_name, norad_id, tz, p):
    def local(t):
        return t.astimezone(tz).isoformat()

    def utc(t):
        return t.utc_iso()

    record = {
        "site": site_name,
        "satellite_name": satellite_name,
        "norad_id": norad_id,
        "rise_time_utc": utc(p["rise_time"]),
        "rise_time_local": local(p["rise_time"]),
        "rise_el_deg": round(p["rise_el"], 2),
        "rise_az_deg": round(p["rise_az"], 2),
        "peak_time_utc": utc(p["peak_time"]),
        "peak_time_local": local(p["peak_time"]),
        "peak_el_deg": round(p["peak_el"], 2),
        "peak_az_deg": round(p["peak_az"], 2),
        "set_time_utc": utc(p["set_time"]),
        "set_time_local": local(p["set_time"]),
        "set_el_deg": round(p["set_el"], 2),
        "set_az_deg": round(p["set_az"], 2),
        "optically_visible": p["optically_visible"],
        "optical_rise_time_local": local(p["optical_rise_time"]) if p["optically_visible"] else None,
        "optical_set_time_local": local(p["optical_set_time"]) if p["optically_visible"] else None,
        "peak_magnitude": round(p["peak_magnitude"], 2) if p.get("peak_magnitude") is not None else None,
    }
    return record


def write_csv(records, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def write_json(records, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def infer_format(path, explicit_format=None):
    if explicit_format:
        return explicit_format.lower()
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext in ("csv", "json"):
        return ext
    raise ValueError(f"Cannot infer output format from path '{path}'; specify output.format as 'csv' or 'json'")


def write_results(records, path, explicit_format=None):
    fmt = infer_format(path, explicit_format)
    if fmt == "csv":
        write_csv(records, path)
    elif fmt == "json":
        write_json(records, path)
    else:
        raise ValueError(f"Unsupported output format: {fmt}")
