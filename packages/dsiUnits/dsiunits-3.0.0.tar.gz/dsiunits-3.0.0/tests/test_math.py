"""Module for testing math operators."""

from __future__ import annotations

import random
from sys import float_info

import pytest

from dsi_unit import DsiUnit
from dsi_unit.unit_mapping import _BASE_DSI_UNIT_MAP, PREFIX_TO_SCALE_MAP  # noqa: PLC2701

# All digital prefixes end in 'bi'.
DIGITAL_PREFIXES_MAP = {p: s for p, s in PREFIX_TO_SCALE_MAP.items() if p.endswith("bi")}


@pytest.fixture
def gen_units() -> dict[str, DsiUnit]:
    """Fixed units to be used at the tests."""
    return {
        "m": DsiUnit(r"\metre"),
        "km": DsiUnit(r"\kilo\metre"),
        "mm": DsiUnit(r"\milli\metre"),
        "s": DsiUnit(r"\second"),
        "V": DsiUnit(r"\volt"),
        "A": DsiUnit(r"\ampere"),
        "mps": DsiUnit(r"\metre\per\second"),
        "one": DsiUnit(r"\one"),
        "ppm": DsiUnit(r"\ppm"),
        "%": DsiUnit(r"\percent"),
    }


def test_unit_multiplication(gen_units: dict[str, DsiUnit]):
    """Testing the __mul__ method at DsiUnit."""
    assert gen_units["m"] * gen_units["s"] == DsiUnit(r"\metre\second")
    assert gen_units["mps"] * gen_units["s"] == gen_units["m"]
    assert gen_units["mps"] * gen_units["m"] == DsiUnit(r"\metre\tothe{2}\second\tothe{-1}")
    assert gen_units["m"] * gen_units["one"] * gen_units["one"] == gen_units["m"]
    assert gen_units["km"] * gen_units["mm"] == DsiUnit(r"\metre\tothe{2}")


def test_unit_division(gen_units: dict[str, DsiUnit]):
    """Testing the __truediv__ method at DsiUnit."""
    assert gen_units["m"] / gen_units["s"] == gen_units["mps"]
    assert gen_units["m"] / gen_units["one"] / gen_units["one"] == gen_units["m"]
    assert gen_units["mps"] / gen_units["s"] == DsiUnit(r"\metre\second\tothe{-2}")


def test_unit_power(gen_units: dict[str, DsiUnit]):
    """Testing the __pow__ method at DsiUnit."""
    assert gen_units["m"] ** 2 == DsiUnit(r"\metre\tothe{2}")
    assert gen_units["mps"] ** 3 == DsiUnit(r"\metre\tothe{3}\second\tothe{-3}")
    assert gen_units["V"] ** 0 == gen_units["one"]


@pytest.mark.parametrize(
    ("unit_name", "base_unit_name", "factor", "digital"),
    [
        (r"\milli\volt", r"\volt", 1e3, False),
        (r"\kilo\metre", r"\metre", 1e-3, False),
        (r"\metre\per\second", r"\kilo\metre\per\hour", 1 / 3.6, False),
        (r"\second", r"\minute", 60, False),
        (r"\joule", r"\electronvolt", 1.6e-19, False),
        (r"\one", r"\percent", 0.01, False),
        (r"\one", r"\ppm", 1e-6, False),
        (r"\bit", r"\byte", 8, True),
        (r"\mebi\bit", r"\kibi\byte", 1 / 128, True),
    ]
    + [(rf"\{pre}\bit", rf"\{pre}\byte", 8, True) for pre in DIGITAL_PREFIXES_MAP]
    + [
        (rf"\{u}", rf"\{pre}\{u}", 1024**idx, True)
        for idx, pre in enumerate(sorted(DIGITAL_PREFIXES_MAP, key=DIGITAL_PREFIXES_MAP.get), start=1)
        for u in ("bit", "byte")
    ],
)
def test_base_unit_conversion(unit_name: str, base_unit_name: str, factor: float, digital: bool):
    """Base checking for the scale factor."""
    unit = DsiUnit(unit_name)
    base_unit = DsiUnit(base_unit_name)

    if not digital and unit_name != r"\joule":
        assert unit.get_base_unit(base_unit) == unit
    scale_factor = unit.get_scale_factor(base_unit)
    assert abs(scale_factor - factor) < float_info.epsilon


@pytest.mark.parametrize(
    ("unit_name", "convert_unit"),
    [
        # Units that cannot be converted to any base unit:
        (r"\bel", random.choice(list(_BASE_DSI_UNIT_MAP))),
        (r"\decibel", random.choice(list(_BASE_DSI_UNIT_MAP))),
        (r"\neper", random.choice(list(_BASE_DSI_UNIT_MAP))),
        (r"\arcminute", random.choice(list(_BASE_DSI_UNIT_MAP))),
        # Incorrect conversions:
        (r"\percent", r"\metre"),
        (r"\barn", r"\kelvin"),
        (r"\day", r"\kilogram"),
    ],
)
def test_invalid_conversion(unit_name: str, convert_unit: str):
    """Checking invalid conversions among units."""
    unit = DsiUnit(unit_name)
    base_unit = DsiUnit(convert_unit)
    # There is no common base unit:
    assert unit.get_base_unit(base_unit) is None
