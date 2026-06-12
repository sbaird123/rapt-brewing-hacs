"""Tests for the session data model and downsampling."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from rapt_brewing.data import (
    Alert,
    BrewingSession,
    DataPoint,
    downsample_data_points,
)


def test_data_point_round_trip():
    point = DataPoint(
        timestamp=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc),
        gravity=1.050,
        temperature=20.5,
        battery_level=85,
        signal_strength=-70,
        gravity_velocity=-5.5,
        accelerometer_x=1.0,
        accelerometer_y=2.0,
        accelerometer_z=3.0,
    )
    restored = DataPoint.from_dict(point.to_dict())
    assert restored == point


def test_data_point_from_legacy_dict_without_new_fields():
    restored = DataPoint.from_dict(
        {"timestamp": "2026-06-01T12:00:00+00:00", "gravity": 1.05}
    )
    assert restored.gravity == 1.05
    assert restored.gravity_velocity is None
    assert restored.accelerometer_x is None


def test_session_round_trip():
    session = BrewingSession(
        id="session_1",
        name="Test Brew",
        original_gravity=1.050,
        target_gravity=1.010,
        state="active",
        started_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        data_points=[
            DataPoint(timestamp=datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc), gravity=1.050)
        ],
        alerts=[
            Alert(type="low_battery", message="Low battery: 10%",
                  timestamp=datetime(2026, 6, 2, tzinfo=timezone.utc))
        ],
        battery_calibrated=True,
    )
    restored = BrewingSession.from_dict(session.to_dict())
    assert restored == session


def test_downsample_keeps_recent_thins_old():
    now = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)
    # One point per minute for 3 days
    points = [
        DataPoint(timestamp=now - timedelta(minutes=i), gravity=1.05)
        for i in range(3 * 24 * 60, 0, -1)
    ]

    result = downsample_data_points(points, now)

    cutoff = now - timedelta(hours=24)
    recent = [dp for dp in result if dp.timestamp >= cutoff]
    old = [dp for dp in result if dp.timestamp < cutoff]

    # All recent points kept at full resolution
    assert len(recent) == 24 * 60
    # Older points thinned to ~one per 15 minutes (2 days ≈ 192 buckets)
    assert len(old) <= 2 * 24 * 4 + 2
    assert len(old) >= 2 * 24 * 4 - 2
    # Chronological order preserved
    assert result == sorted(result, key=lambda dp: dp.timestamp)


def test_downsample_noop_for_recent_only():
    now = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)
    points = [
        DataPoint(timestamp=now - timedelta(minutes=i), gravity=1.05)
        for i in range(60, 0, -1)
    ]
    assert downsample_data_points(points, now) == points
