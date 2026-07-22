from skyfield.api import wgs84


def find_passes(satellite, latitude_deg, longitude_deg, elevation_m, t0, t1, elevation_mask_deg=0.0):
    topos = wgs84.latlon(latitude_deg, longitude_deg, elevation_m)
    times, events = satellite.find_events(topos, t0, t1, altitude_degrees=elevation_mask_deg)

    difference = satellite - topos

    passes = []
    current = None
    for t, event in zip(times, events):
        alt, az, _ = difference.at(t).altaz()

        if event == 0:
            current = {"rise_time": t, "rise_az": az.degrees, "rise_el": alt.degrees}
        elif event == 1:
            if current is None:
                continue
            current["peak_time"] = t
            current["peak_az"] = az.degrees
            current["peak_el"] = alt.degrees
        elif event == 2:
            if current is None or "peak_time" not in current:
                current = None
                continue
            current["set_time"] = t
            current["set_az"] = az.degrees
            current["set_el"] = alt.degrees
            passes.append(current)
            current = None

    return passes
