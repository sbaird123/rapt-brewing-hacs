"""Tests for RAPT Brew Stream webhook payload parsing."""
from __future__ import annotations

import pytest

from rapt_brewing.brew_stream import parse_brew_stream_payload


def test_parse_brew_stream_envelope():
    parsed = parse_brew_stream_payload(
        {
            "event": "telemetry",
            "deviceId": "pill-1",
            "data": {"temperature": 20.5, "gravity": 1.0505, "battery": 85.2, "rssi": -70.4},
        }
    )

    assert parsed == {
        "gravity": pytest.approx(1.0505),
        "temperature": pytest.approx(20.5),
        "battery": 85,
        "signal_strength": -70,
    }


def test_parse_flat_payload_in_gravity_points():
    parsed = parse_brew_stream_payload({"gravity": "1050", "temperature": "20"})

    assert parsed["gravity"] == pytest.approx(1.050)


def test_parse_fahrenheit_converted_to_celsius():
    parsed = parse_brew_stream_payload({"temperature": 68, "temp_units": "F"})

    assert parsed["temperature"] == pytest.approx(20.0)


def test_parse_non_telemetry_event_ignored():
    assert parse_brew_stream_payload({"event": "alert", "data": {"gravity": 1.05}}) is None


def test_parse_payload_without_readings_ignored():
    assert parse_brew_stream_payload({"event": "telemetry", "data": {"rssi": -60}}) is None


@pytest.mark.parametrize("payload", [None, [], "text", {"data": "text"}])
def test_parse_malformed_payload_ignored(payload):
    assert parse_brew_stream_payload(payload) is None


def test_parse_non_numeric_reading_ignored():
    assert parse_brew_stream_payload({"gravity": "bad", "temperature": 20})["gravity"] is None
