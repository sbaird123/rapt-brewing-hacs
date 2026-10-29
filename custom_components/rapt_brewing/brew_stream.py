"""Parse RAPT Brew Stream webhook payloads.

Pill firmware 2.0.0+ reports to the RAPT Brew platform (brew.rapt.io), which
has no polling API; Brew Streams push telemetry to a webhook instead. RAPT has
not documented the payload, so this accepts the observed envelope
``{"event": "telemetry", "deviceId": ..., "data": {...}}`` as well as a flat
object of readings.
"""
from __future__ import annotations

from typing import Any

# Gravity above this is in gravity points (1050 == 1.050 SG), not SG
_GRAVITY_POINTS_THRESHOLD = 2.0


def _number(value: Any) -> float | None:
    """Coerce a reading to float, treating anything non-numeric as missing."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_brew_stream_payload(payload: Any) -> dict[str, Any] | None:
    """Normalise a Brew Stream payload into sensor values.

    Returns None for payloads that are not telemetry or carry no readings.
    Gravity is returned in SG and temperature in °C.
    """
    if not isinstance(payload, dict):
        return None
    if payload.get("event", "telemetry") != "telemetry":
        return None
    reading = payload.get("data", payload)
    if not isinstance(reading, dict):
        return None

    gravity = _number(reading.get("gravity"))
    if gravity is not None and gravity > _GRAVITY_POINTS_THRESHOLD:
        gravity /= 1000.0

    temperature = _number(reading.get("temperature"))
    units = reading.get("temp_units", payload.get("temp_units"))
    if temperature is not None and str(units).upper() == "F":
        temperature = (temperature - 32.0) * 5.0 / 9.0

    battery = _number(reading.get("battery"))
    rssi = _number(reading.get("rssi"))

    if gravity is None and temperature is None and battery is None:
        return None

    return {
        "gravity": gravity,
        "temperature": temperature,
        "battery": int(round(battery)) if battery is not None else None,
        "signal_strength": int(round(rssi)) if rssi is not None else None,
    }
