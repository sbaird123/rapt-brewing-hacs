"""Tests for unit conversion helpers."""
from __future__ import annotations

import pytest

from rapt_brewing.util import sg_to_plato


def test_water_is_zero_plato():
    assert sg_to_plato(1.000) == pytest.approx(0.0, abs=0.01)


def test_typical_wort():
    # 1.040 SG ≈ 10 °P
    assert sg_to_plato(1.040) == pytest.approx(10.0, abs=0.05)
    # 1.048 SG ≈ 11.9 °P
    assert sg_to_plato(1.048) == pytest.approx(11.9, abs=0.05)


def test_high_gravity_wort():
    # 1.080 SG ≈ 19.3 °P
    assert sg_to_plato(1.080) == pytest.approx(19.3, abs=0.1)
