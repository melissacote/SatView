from zoneinfo import ZoneInfo

from timezonefinder import TimezoneFinder

_finder = TimezoneFinder()


def resolve_timezone(latitude_deg, longitude_deg):
    tz_name = _finder.timezone_at(lat=latitude_deg, lng=longitude_deg)
    if tz_name is None:
        raise ValueError(
            f"Could not resolve a timezone for lat={latitude_deg}, lon={longitude_deg}"
        )
    return ZoneInfo(tz_name)
