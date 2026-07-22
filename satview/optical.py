from skyfield.api import wgs84

from satview.cache_loader import loader as default_loader
from satview.magnitude import estimate_apparent_magnitude

TWILIGHT_SUN_ALTITUDE_DEG = -6.0  # civil twilight: sky dark enough to see satellites
SAMPLE_STEP_SECONDS = 2.0


def load_ephemeris(loader=None):
    loader = loader or default_loader
    return loader("de421.bsp")


def is_pass_moment_optically_visible(eph, satellite, observer, t):
    sat_sunlit = satellite.at(t).is_sunlit(eph)

    sun_alt, _, _ = observer.at(t).observe(eph["sun"]).apparent().altaz()
    sky_dark = sun_alt.degrees < TWILIGHT_SUN_ALTITUDE_DEG

    return bool(sat_sunlit) and sky_dark


def find_optical_subwindow(eph, satellite, latitude_deg, longitude_deg, elevation_m, rise_time, set_time, ts):
    topos = wgs84.latlon(latitude_deg, longitude_deg, elevation_m)
    observer = eph["earth"] + topos

    duration_seconds = (set_time.tt - rise_time.tt) * 86400.0
    n_samples = max(2, int(duration_seconds / SAMPLE_STEP_SECONDS) + 1)

    step_days = (set_time.tt - rise_time.tt) / (n_samples - 1)
    sample_times = ts.tt_jd([rise_time.tt + i * step_days for i in range(n_samples)])

    visible_flags = [
        is_pass_moment_optically_visible(eph, satellite, observer, sample_times[i])
        for i in range(n_samples)
    ]

    if not any(visible_flags):
        return None

    first_idx = visible_flags.index(True)
    last_idx = len(visible_flags) - 1 - visible_flags[::-1].index(True)

    return {
        "optical_rise_time": sample_times[first_idx],
        "optical_set_time": sample_times[last_idx],
    }


def annotate_pass_with_optical_visibility(eph, satellite, norad_id, latitude_deg, longitude_deg, elevation_m, p, ts):
    subwindow = find_optical_subwindow(
        eph, satellite, latitude_deg, longitude_deg, elevation_m, p["rise_time"], p["set_time"], ts
    )
    if subwindow is None:
        p["optically_visible"] = False
        p["peak_magnitude"] = None
    else:
        p["optically_visible"] = True
        p["optical_rise_time"] = subwindow["optical_rise_time"]
        p["optical_set_time"] = subwindow["optical_set_time"]

        topos = wgs84.latlon(latitude_deg, longitude_deg, elevation_m)
        p["peak_magnitude"] = estimate_apparent_magnitude(
            eph, satellite, topos, norad_id, p["peak_time"], elevation_deg=p["peak_el"]
        )
    return p
