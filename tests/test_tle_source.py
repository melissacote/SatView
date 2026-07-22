import pytest

from satview.tle_source import fetch_satellite


class FakeSatellite:
    def __init__(self, name):
        self.name = name


class FakeLoader:
    """Stands in for skyfield's Loader so fallback logic can be tested offline."""

    def __init__(self, live_fails=False, cached_exists=False, cached_age_days=1.0, live_returns_empty=False):
        self.live_fails = live_fails
        self.cached_exists = cached_exists
        self.cached_age_days = cached_age_days
        self.live_returns_empty = live_returns_empty
        self.calls = []

    def tle_file(self, url, filename, reload):
        self.calls.append(reload)
        if reload:
            if self.live_fails:
                raise OSError("simulated network failure")
            if self.live_returns_empty:
                return []
            return [FakeSatellite("LIVE SAT")]
        return [FakeSatellite("CACHED SAT")]

    def exists(self, filename):
        return self.cached_exists

    def days_old(self, filename):
        return self.cached_age_days


def test_live_fetch_success_returns_satellite():
    loader = FakeLoader()
    sat = fetch_satellite(25544, loader=loader)
    assert sat.name == "LIVE SAT"
    assert loader.calls == [True]


def test_live_fetch_empty_result_raises():
    loader = FakeLoader(live_returns_empty=True)
    with pytest.raises(ValueError, match="No TLE returned"):
        fetch_satellite(25544, loader=loader)


def test_live_fetch_fails_falls_back_to_cache():
    loader = FakeLoader(live_fails=True, cached_exists=True, cached_age_days=3.5)
    sat = fetch_satellite(25544, loader=loader)
    assert sat.name == "CACHED SAT"
    assert loader.calls == [True, False]


def test_live_fetch_fails_and_no_cache_raises():
    loader = FakeLoader(live_fails=True, cached_exists=False)
    with pytest.raises(ValueError, match="no cached copy"):
        fetch_satellite(25544, loader=loader)
