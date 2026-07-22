from satview.cache_loader import loader as default_loader

CELESTRAK_GP_URL = "https://celestrak.org/NORAD/elements/gp.php?CATNR={norad_id}&FORMAT=TLE"


def fetch_satellite(norad_id, loader=None):
    loader = loader or default_loader
    url = CELESTRAK_GP_URL.format(norad_id=norad_id)
    filename = f"tle_{norad_id}.txt"

    try:
        satellites = loader.tle_file(url, filename=filename, reload=True)
        if not satellites:
            raise ValueError(f"No TLE returned for NORAD ID {norad_id}")
        return satellites[0]
    except Exception as fetch_error:
        if not loader.exists(filename):
            raise ValueError(
                f"Could not fetch TLE for NORAD ID {norad_id} ({fetch_error}), "
                f"and no cached copy is available"
            ) from fetch_error

        age_days = loader.days_old(filename)
        print(
            f"WARNING: live TLE fetch for NORAD {norad_id} failed ({fetch_error}); "
            f"falling back to cached copy, {age_days:.1f} day(s) old"
        )
        satellites = loader.tle_file(url, filename=filename, reload=False)
        if not satellites:
            raise ValueError(f"Cached TLE file for NORAD ID {norad_id} is unusable") from fetch_error
        return satellites[0]
