"""Pure helper functions for RAPT Brewing (no Home Assistant dependencies)."""
from __future__ import annotations

# Gravity readings are corrected to this reference temperature
CALIBRATION_TEMPERATURE_C = 20.0
# Typical apparent attenuation, used to guess a target when none is set
DEFAULT_APPARENT_ATTENUATION = 0.75
MAX_ABV = 20.0


def sg_to_plato(sg: float) -> float:
    """Convert specific gravity to degrees Plato (ASBC polynomial)."""
    return -616.868 + 1111.14 * sg - 630.272 * sg**2 + 135.997 * sg**3


def _water_density_factor(temperature_c: float) -> float:
    """Relative density of water at a temperature (standard brewing polynomial, °F)."""
    f = temperature_c * 9.0 / 5.0 + 32.0
    return 1.00130346 - 0.000134722124 * f + 0.00000204052596 * f**2 - 0.00000000232820948 * f**3


def temperature_corrected_gravity(gravity: float, temperature_c: float) -> float:
    """Correct a gravity reading to what it would read at 20 °C.

    Warm wort is less dense and reads low; cold wort reads high.
    """
    return gravity * (
        _water_density_factor(temperature_c)
        / _water_density_factor(CALIBRATION_TEMPERATURE_C)
    )


def abv(original_gravity: float, current_gravity: float) -> float:
    """Alcohol by volume (%) from original and current gravity.

    Uses the continuous "alternative" formula, which stays accurate for
    stronger beers where the simple 131.25 × (OG − FG) under-reads.
    """
    if current_gravity >= original_gravity:
        return 0.0
    value = (
        76.08 * (original_gravity - current_gravity) / (1.775 - original_gravity)
        * (current_gravity / 0.794)
    )
    return min(value, MAX_ABV)


def default_target_gravity(original_gravity: float) -> float:
    """Guess a final gravity from the original gravity at typical attenuation."""
    return 1.0 + (original_gravity - 1.0) * (1.0 - DEFAULT_APPARENT_ATTENUATION)
