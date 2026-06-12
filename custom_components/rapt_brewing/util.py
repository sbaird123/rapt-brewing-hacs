"""Pure helper functions for RAPT Brewing (no Home Assistant dependencies)."""
from __future__ import annotations


def sg_to_plato(sg: float) -> float:
    """Convert specific gravity to degrees Plato (ASBC polynomial)."""
    return -616.868 + 1111.14 * sg - 630.272 * sg**2 + 135.997 * sg**3
