import math
import os

CATALOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "qsmag.txt")

_catalog_cache = None


def _parse_catalog(path):
    catalog = {}
    with open(path, encoding="latin-1") as f:
        next(f)  # header line
        for line in f:
            if len(line) < 39:
                continue
            norad_field = line[0:5].strip()
            mag_field = line[33:39].strip()
            if not norad_field.isdigit() or not mag_field:
                continue
            try:
                catalog[int(norad_field)] = float(mag_field)
            except ValueError:
                continue
    return catalog


def load_catalog():
    global _catalog_cache
    if _catalog_cache is None:
        _catalog_cache = _parse_catalog(CATALOG_PATH)
    return _catalog_cache


def standard_magnitude(norad_id):
    return load_catalog().get(norad_id)


def _phase_angle_and_range_km(eph, satellite, topos, t):
    earth = eph["earth"]
    sun = eph["sun"]

    sat_vec = satellite.at(t).position.km
    sun_vec = (sun - earth).at(t).position.km
    obs_vec = topos.at(t).position.km

    sat_to_observer = obs_vec - sat_vec
    sat_to_sun = sun_vec - sat_vec

    range_km = math.sqrt(sum(c * c for c in sat_to_observer))
    sun_dist = math.sqrt(sum(c * c for c in sat_to_sun))

    dot = sum(a * b for a, b in zip(sat_to_observer, sat_to_sun))
    cos_phase = dot / (range_km * sun_dist)
    cos_phase = max(-1.0, min(1.0, cos_phase))
    phase_angle_rad = math.acos(cos_phase)

    return phase_angle_rad, range_km


EXTINCTION_COEFFICIENT_MAG_PER_AIRMASS = 0.25  # typical clear-sky V-band value at sea level


def airmass(elevation_deg):
    # Kasten & Young (1989); stays finite all the way down to the horizon.
    return 1.0 / (
        math.sin(math.radians(elevation_deg))
        + 0.50572 * (elevation_deg + 6.07995) ** -1.6364
    )


def estimate_apparent_magnitude(eph, satellite, topos, norad_id, t, elevation_deg=None):
    std_mag = standard_magnitude(norad_id)
    if std_mag is None:
        return None

    phase_angle_rad, range_km = _phase_angle_and_range_km(eph, satellite, topos, t)

    illumination_term = 1.0 + math.cos(phase_angle_rad)
    if illumination_term <= 0:
        return None  # satellite's dark side faces the observer

    apparent_mag = std_mag + 5.0 * math.log10(range_km / 1000.0) - 2.5 * math.log10(illumination_term)

    if elevation_deg is not None:
        apparent_mag += EXTINCTION_COEFFICIENT_MAG_PER_AIRMASS * airmass(elevation_deg)

    return apparent_mag
