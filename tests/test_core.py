"""Tests for phi_engine core transforms and energy conservation."""
from math import pi

from phi_engine.core import (
    BRAHIM_NUMBERS,
    LUCAS_NUMBERS,
    PHI,
    D,
    Energy,
    Theta,
    fib,
    lucas,
    mirror,
    x_from_D,
)


def test_phi_value():
    assert abs(PHI - 1.6180339887498949) < 1e-15


def test_d_inverse():
    """D(x) + D(1/x) = 0 for all x > 0."""
    for x in [0.1, 0.5, 1.0, 2.0, 42.0, 1000.0]:
        assert abs(D(x) + D(1.0 / x)) < 1e-10


def test_x_from_d_roundtrip():
    for x in [0.01, 0.5, 1.0, 3.14, 100.0]:
        assert abs(x_from_D(D(x)) - x) < 1e-10


def test_energy_conservation():
    """Energy(x) = 2*pi for all x > 0."""
    for x in [0.001, 0.5, 1.0, PHI, 42.0, 9999.0]:
        assert abs(Energy(x) - 2 * pi) < 1e-10


def test_theta():
    assert abs(Theta(1.0) - 2 * pi) < 1e-10
    assert abs(Theta(0.5) - pi) < 1e-10


def test_fib_sequence():
    assert fib(0) == 0
    assert fib(1) == 1
    assert fib(10) == 55


def test_lucas_matches_table():
    for i, expected in enumerate(LUCAS_NUMBERS, start=1):
        assert lucas(i) == expected


def test_mirror_involution():
    for b in BRAHIM_NUMBERS:
        assert mirror(mirror(b)) == b


def test_brahim_sum():
    assert sum(BRAHIM_NUMBERS) == 1070
