"""Tests for the RAPT Pill BLE advertisement parser."""
from __future__ import annotations

import struct

import pytest

from rapt_brewing.ble_device import (
    KEGLAND_MANUFACTURER_ID,
    RAPT_MANUFACTURER_ID,
    RAPTPillBLEParser,
    RAPTPillBluetoothDeviceData,
)

from conftest import FakeServiceInfo

TEMP_20_5_C = int((20.5 + 273.15) * 128)


def make_v1_packet(gravity_points: float = 1050.0, battery_pct: int = 85) -> bytes:
    return b"PT" + struct.pack(
        ">B6sHfhhhh",
        1,
        bytes.fromhex("78e36d001122"),
        TEMP_20_5_C,
        gravity_points,
        16, 16, 1600,
        battery_pct * 256,
    )


def make_v2_packet(gravity_points: float = 1012.0, velocity: float = -5.5,
                   velocity_valid: int = 1, battery_pct: int = 42) -> bytes:
    return b"PT" + struct.pack(
        ">BBBfHfhhhh",
        2, 0, velocity_valid, velocity,
        TEMP_20_5_C, gravity_points,
        16, 16, 1600,
        battery_pct * 256,
    )


def test_v1_packet_parses():
    parser = RAPTPillBLEParser()
    data = parser.parse_advertisement(FakeServiceInfo({RAPT_MANUFACTURER_ID: make_v1_packet()}))

    assert data is not None
    assert data.temperature == pytest.approx(20.5, abs=0.01)
    assert data.gravity == pytest.approx(1.050, abs=0.0001)
    assert data.battery == 85
    assert data.data_format_version == 1
    assert data.mac_address == "78:e3:6d:00:11:22"
    assert data.accelerometer_x == pytest.approx(1.0)
    assert data.accelerometer_z == pytest.approx(100.0)


def test_v2_packet_parses_with_velocity():
    parser = RAPTPillBLEParser()
    data = parser.parse_advertisement(FakeServiceInfo({RAPT_MANUFACTURER_ID: make_v2_packet()}))

    assert data is not None
    assert data.gravity == pytest.approx(1.012, abs=0.0001)
    assert data.gravity_velocity == pytest.approx(-5.5)
    assert data.gravity_velocity_valid is True
    assert data.battery == 42
    assert data.data_format_version == 2


def test_v2_invalid_velocity_is_none():
    parser = RAPTPillBLEParser()
    data = parser.parse_advertisement(
        FakeServiceInfo({RAPT_MANUFACTURER_ID: make_v2_packet(velocity=99.0, velocity_valid=0)})
    )

    assert data is not None
    assert data.gravity_velocity is None
    assert data.gravity_velocity_valid is False


def test_firmware_version_attached_to_telemetry():
    parser = RAPTPillBLEParser()
    # Firmware-only advertisement is not new telemetry
    assert parser.parse_advertisement(
        FakeServiceInfo({KEGLAND_MANUFACTURER_ID: b"G" + b"v1.2.3"})
    ) is None

    data = parser.parse_advertisement(FakeServiceInfo({RAPT_MANUFACTURER_ID: make_v2_packet()}))
    assert data is not None
    assert data.firmware_version == "v1.2.3"


def test_stale_advertisement_returns_none_but_keeps_last_data():
    parser = RAPTPillBLEParser()
    data = parser.parse_advertisement(FakeServiceInfo({RAPT_MANUFACTURER_ID: make_v1_packet()}))
    assert data is not None

    assert parser.parse_advertisement(FakeServiceInfo({999: b"junk"})) is None
    assert parser.last_data is data


def test_short_packet_rejected():
    parser = RAPTPillBLEParser()
    assert parser.parse_advertisement(
        FakeServiceInfo({RAPT_MANUFACTURER_ID: b"PT\x01short"})
    ) is None


def test_unknown_version_rejected():
    packet = b"PT" + bytes([9]) + bytes(20)
    parser = RAPTPillBLEParser()
    assert parser.parse_advertisement(FakeServiceInfo({RAPT_MANUFACTURER_ID: packet})) is None


def test_device_data_tracks_freshness():
    device = RAPTPillBluetoothDeviceData("RAPT Pill TEST")
    assert device.last_telemetry_at is None

    service_info = FakeServiceInfo({RAPT_MANUFACTURER_ID: make_v1_packet()})
    device.handle_advertisement(service_info)

    assert device.get_last_sensor_data() is not None
    assert device.get_last_service_info() is service_info
    first_seen = device.last_telemetry_at
    assert first_seen is not None

    # A non-telemetry advertisement must not bump the freshness marker
    device.handle_advertisement(FakeServiceInfo({999: b"junk"}))
    assert device.last_telemetry_at == first_seen
