import math

import pytest

from satview.magnitude import airmass, standard_magnitude


def test_standard_magnitude_known_satellite():
    assert standard_magnitude(25544) == pytest.approx(-2.5)


def test_standard_magnitude_unknown_satellite_returns_none():
    assert standard_magnitude(999999999) is None


def test_airmass_at_zenith_is_approximately_one():
    assert airmass(90.0) == pytest.approx(1.0, abs=0.01)


def test_airmass_increases_as_elevation_decreases():
    assert airmass(10.0) > airmass(45.0) > airmass(90.0)


def test_airmass_finite_at_horizon():
    value = airmass(0.0)
    assert math.isfinite(value)
    assert value > 5.0
