"""Tests for unit conversion helpers."""
from __future__ import annotations

import pytest

from rapt_brewing.util import (
    abv,
    default_target_gravity,
    sg_to_plato,
    temperature_corrected_gravity,
)


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


def test_no_temperature_correction_at_20c():
    assert temperature_corrected_gravity(1.050, 20.0) == pytest.approx(1.050, abs=1e-6)


def test_warm_wort_reads_low_so_correction_raises_it():
    # Standard hydrometer tables: 1.050 read at 30 °C is about 1.0526 at 20 °C
    assert temperature_corrected_gravity(1.050, 30.0) == pytest.approx(1.0526, abs=0.0002)


def test_cold_wort_reads_high_so_correction_lowers_it():
    # A cold crash at 2 °C reads about 2 points high
    assert temperature_corrected_gravity(1.012, 2.0) == pytest.approx(1.0101, abs=0.0002)


def test_abv_typical_beer():
    assert abv(1.050, 1.010) == pytest.approx(5.34, abs=0.01)


def test_abv_is_continuous_across_former_gravity_steps():
    assert abv(1.0601, 1.012) == pytest.approx(abv(1.0599, 1.012), abs=0.05)


def test_abv_zero_before_fermentation_starts():
    assert abv(1.050, 1.051) == 0.0


def test_default_target_gravity_scales_with_original_gravity():
    # 75% apparent attenuation: a strong beer must not get a mid-ferment target
    assert default_target_gravity(1.080) == pytest.approx(1.020)
