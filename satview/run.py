import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from skyfield.api import load

from satview.config import load_config
from satview.tle_source import fetch_satellite
from satview.passes import find_passes
from satview.location import resolve_timezone
from satview.optical import load_ephemeris, annotate_pass_with_optical_visibility
from satview.output import build_record, write_results


def fmt(t, tz):
    return t.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S %Z")


def parse_start_time(value, ts):
    if value == "now":
        return ts.now()
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return ts.from_datetime(dt)


def print_pass(p, tz, indent="  "):
    print(f"{indent}  Rise:  {fmt(p['rise_time'], tz)}  el {p['rise_el']:5.1f}deg  az {p['rise_az']:6.1f}deg")
    print(f"{indent}  Peak:  {fmt(p['peak_time'], tz)}  el {p['peak_el']:5.1f}deg  az {p['peak_az']:6.1f}deg")
    print(f"{indent}  Set:   {fmt(p['set_time'], tz)}  el {p['set_el']:5.1f}deg  az {p['set_az']:6.1f}deg")
    if p["optically_visible"]:
        mag = p["peak_magnitude"]
        mag_str = f"{mag:.1f}" if mag is not None else "N/A (no catalog data)"
        print(
            f"{indent}  Optically visible: yes "
            f"({fmt(p['optical_rise_time'], tz)} - {fmt(p['optical_set_time'], tz)}), "
            f"mag {mag_str} at peak"
        )
    else:
        print(f"{indent}  Optically visible: no")


def run(config):
    ts = load.timescale()
    eph = load_ephemeris()

    t0 = parse_start_time(config["search"]["start"], ts)
    hours = config["search"]["hours"]
    t1 = ts.tt_jd(t0.tt + hours / 24.0)
    elevation_mask_deg = config["elevation_mask_deg"]

    satellites = {}
    for sat_cfg in config["satellites"]:
        norad_id = sat_cfg["norad_id"]
        try:
            satellites[norad_id] = fetch_satellite(norad_id)
        except ValueError as e:
            print(f"WARNING: skipping NORAD {norad_id}: {e}")

    records = []

    for site in config["sites"]:
        lat, lon, elev_m = site["latitude"], site["longitude"], site["elevation_m"]
        try:
            tz = resolve_timezone(lat, lon)
        except ValueError as e:
            print(f"WARNING: {e}; falling back to UTC for site '{site['name']}'")
            tz = ZoneInfo("UTC")

        print(f"\n=== Site: {site['name']} (lat={lat}, lon={lon}, tz={tz.key}) ===")

        for sat_cfg in config["satellites"]:
            norad_id = sat_cfg["norad_id"]
            satellite = satellites.get(norad_id)
            if satellite is None:
                continue  # already warned above

            print(f"\n--- {satellite.name} (NORAD {norad_id}) ---")

            try:
                passes = find_passes(
                    satellite, lat, lon, elev_m, t0, t1, elevation_mask_deg=elevation_mask_deg
                )
                passes = [
                    annotate_pass_with_optical_visibility(eph, satellite, norad_id, lat, lon, elev_m, p, ts)
                    for p in passes
                ]
            except Exception as e:
                print(f"  WARNING: could not compute passes for NORAD {norad_id} at '{site['name']}': {e}")
                continue

            if not passes:
                print("  No passes found in window.")
                continue

            for i, p in enumerate(passes, 1):
                print(f"  Pass {i}:")
                print_pass(p, tz)
                records.append(build_record(site["name"], satellite.name, norad_id, tz, p))

    if config.get("output"):
        write_results(records, config["output"]["path"], config["output"]["format"])
        print(f"\nWrote {len(records)} pass record(s) to {config['output']['path']}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m satview.run <config.yaml>")
        sys.exit(1)

    try:
        config = load_config(sys.argv[1])
    except ValueError as e:
        print(f"Config error: {e}")
        sys.exit(1)

    run(config)


if __name__ == "__main__":
    main()
