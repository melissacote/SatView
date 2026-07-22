import pytest

import satview.location as location


def test_resolve_timezone_known_coordinates():
    tz = location.resolve_timezone(40.7580, -73.9855)
    assert tz.key == "America/New_York"


class _StubFinder:
    def timezone_at(self, lat, lng):
        return None


def test_resolve_timezone_raises_when_unresolvable(monkeypatch):
    monkeypatch.setattr(location, "_finder", _StubFinder())
    with pytest.raises(ValueError, match="Could not resolve"):
        location.resolve_timezone(0.0, 0.0)
