"""Tests for RAPT cloud API response parsing."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from rapt_brewing.api import parse_telemetry_record


def test_parse_full_record():
    parsed = parse_telemetry_record(
        {
            "gravity": 1050.5,
            "temperature": 20.5,
            "battery": 85.2,
            "rssi": -70.4,
            "createdOn": "2026-06-01T10:00:00Z",
            "version": "v1.2.3",
        }
    )

    assert parsed["gravity"] == pytest.approx(1.0505)
    assert parsed["temperature"] == pytest.approx(20.5)
    assert parsed["battery"] == 85
    assert parsed["signal_strength"] == -70
    assert parsed["created_on"] == datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)
    assert parsed["version"] == "v1.2.3"


def test_parse_naive_timestamp_assumed_utc():
    parsed = parse_telemetry_record({"createdOn": "2026-06-01T10:00:00"})
    assert parsed["created_on"] == datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc)


def test_parse_missing_fields_are_none():
    parsed = parse_telemetry_record({})
    assert parsed["gravity"] is None
    assert parsed["temperature"] is None
    assert parsed["battery"] is None
    assert parsed["signal_strength"] is None
    assert parsed["created_on"] is None


def test_parse_bad_timestamp_is_none():
    parsed = parse_telemetry_record({"createdOn": "not-a-date"})
    assert parsed["created_on"] is None
