"""BLE device handler for RAPT Pill integration."""
from __future__ import annotations

import logging
import struct
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import homeassistant.util.dt as dt_util
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

_LOGGER = logging.getLogger(__name__)

# RAPT Pill Bluetooth manufacturer IDs. The first two ASCII bytes of the
# advertisement ("RA" of "RAPT", "KE" of "KEG") are consumed as the little
# endian manufacturer ID, so the manufacturer data payload starts at the
# third byte ("PT..." / "G...").
RAPT_MANUFACTURER_ID = 16722  # 0x4152 - "RA" from RAPT
KEGLAND_MANUFACTURER_ID = 17739  # 0x454B - "KE" from KEG

# Data start patterns for manufacturer data
RAPT_DATA_START = [80, 84]  # "PT" - Pill Telemetry
KEGLAND_DATA_START = [71]   # "G" - General/Version

# Telemetry payload after the "PT" prefix: version byte + 20 data bytes
TELEMETRY_PAYLOAD_LENGTH = 21
V1_STRUCT = ">B6sHfhhhh"   # version + MAC + temp + gravity + accel xyz + battery
V2_STRUCT = ">BBBfHfhhhh"  # version + reserved + velocity_valid + velocity + temp + gravity + accel xyz + battery


@dataclass
class RAPTPillSensorData:
    """RAPT Pill sensor data."""

    temperature: float | None = None
    gravity: float | None = None
    gravity_velocity: float | None = None
    gravity_velocity_valid: bool = False
    battery: int | None = None
    signal_strength: int | None = None
    accelerometer_x: float | None = None
    accelerometer_y: float | None = None
    accelerometer_z: float | None = None
    firmware_version: str | None = None
    device_type: str | None = None
    mac_address: str | None = None
    data_format_version: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "temperature": self.temperature,
            "gravity": self.gravity,
            "gravity_velocity": self.gravity_velocity,
            "gravity_velocity_valid": self.gravity_velocity_valid,
            "battery": self.battery,
            "signal_strength": self.signal_strength,
            "accelerometer_x": self.accelerometer_x,
            "accelerometer_y": self.accelerometer_y,
            "accelerometer_z": self.accelerometer_z,
            "firmware_version": self.firmware_version,
            "device_type": self.device_type,
            "mac_address": self.mac_address,
            "data_format_version": self.data_format_version,
        }


class RAPTPillBLEParser:
    """Parser for RAPT Pill BLE advertisements."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self.last_data: RAPTPillSensorData | None = None
        self.last_telemetry_at: datetime | None = None
        self._firmware_version: str | None = None

    def parse_advertisement(
        self, service_info: BluetoothServiceInfoBleak
    ) -> RAPTPillSensorData | None:
        """Parse BLE advertisement data.

        Returns newly parsed telemetry, or None when the advertisement did not
        contain new telemetry (so callers can distinguish fresh from stale data).
        """
        manufacturer_data = service_info.manufacturer_data

        _LOGGER.debug("RAPT PARSER: Received manufacturer data: %s",
                      {k: v.hex() for k, v in manufacturer_data.items()})

        # KegLand manufacturer data carries the firmware version ("KEG" + version
        # string, with "KE" consumed as the manufacturer ID).
        if KEGLAND_MANUFACTURER_ID in manufacturer_data:
            data = manufacturer_data[KEGLAND_MANUFACTURER_ID]
            if len(data) > 1 and data[0] == KEGLAND_DATA_START[0]:
                firmware = data[1:].decode("utf-8", errors="ignore").strip()
                if firmware:
                    self._firmware_version = firmware
                    _LOGGER.debug("RAPT PARSER: Firmware version: %s", firmware)

        if RAPT_MANUFACTURER_ID in manufacturer_data:
            data = manufacturer_data[RAPT_MANUFACTURER_ID]
            _LOGGER.debug("RAPT PARSER: RAPT data length=%d, hex=%s", len(data), data.hex())
            if len(data) >= 2 and list(data[:2]) == RAPT_DATA_START:
                parsed_data = self._parse_telemetry(data)
                if parsed_data:
                    parsed_data.firmware_version = self._firmware_version
                    self.last_data = parsed_data
                    self.last_telemetry_at = dt_util.utcnow()
                    _LOGGER.debug("RAPT PARSER: Successfully parsed data: temp=%.2f, gravity=%.4f",
                                  parsed_data.temperature or 0, parsed_data.gravity or 0)
                    return parsed_data
                _LOGGER.warning("RAPT PARSER: Failed to parse telemetry data: %s", data.hex())
            else:
                _LOGGER.debug("RAPT PARSER: Data doesn't start with PT prefix: %s", data[:2].hex())

        return None

    def _parse_telemetry(self, data: bytes) -> RAPTPillSensorData | None:
        """Parse a "PT"-prefixed telemetry packet."""
        payload = data[2:]
        if len(payload) < TELEMETRY_PAYLOAD_LENGTH:
            _LOGGER.warning("RAPT telemetry payload too short: %d bytes (need %d): %s",
                            len(payload), TELEMETRY_PAYLOAD_LENGTH, payload.hex())
            return None

        try:
            format_version = payload[0]
            if format_version == 1:
                return self._parse_v1_format(payload)
            if format_version == 2:
                return self._parse_v2_format(payload)
            _LOGGER.warning("Unknown RAPT format version: %d", format_version)
            return None
        except Exception as e:
            _LOGGER.error("Error parsing RAPT telemetry: %s", e)
            return None

    def _parse_v1_format(self, payload: bytes) -> RAPTPillSensorData | None:
        """Parse v1 format: 0x01 mm mm mm mm mm mm tt tt gg gg gg gg xx xx yy yy zz zz bb bb"""
        try:
            unpacked = struct.unpack(V1_STRUCT, payload[:TELEMETRY_PAYLOAD_LENGTH])

            version = unpacked[0]
            mac_bytes = unpacked[1]
            temp_raw = unpacked[2]
            gravity_float = unpacked[3]
            accel_x_raw = unpacked[4]
            accel_y_raw = unpacked[5]
            accel_z_raw = unpacked[6]
            battery_raw = unpacked[7]

            # Convert using official RAPT formulas
            temperature = temp_raw / 128.0 - 273.15  # Kelvin to Celsius
            gravity = gravity_float / 1000.0
            battery = int(battery_raw / 256.0)
            accel_x = accel_x_raw / 16.0
            accel_y = accel_y_raw / 16.0
            accel_z = accel_z_raw / 16.0
            mac_address = ':'.join(f'{b:02x}' for b in mac_bytes)

            _LOGGER.debug("v1 - temp=%.2f°C, gravity=%.4f, battery=%d%%, accel=(%.2f,%.2f,%.2f)",
                          temperature, gravity, battery, accel_x, accel_y, accel_z)

            return RAPTPillSensorData(
                temperature=temperature,
                gravity=gravity,
                battery=battery,
                accelerometer_x=accel_x,
                accelerometer_y=accel_y,
                accelerometer_z=accel_z,
                mac_address=mac_address,
                data_format_version=version,
            )

        except struct.error as e:
            _LOGGER.error("v1 struct unpack failed: %s", e)
            return None

    def _parse_v2_format(self, payload: bytes) -> RAPTPillSensorData | None:
        """Parse v2 format: 0x02 0x00 cc vv vv vv vv tt tt gg gg gg gg xx xx yy yy zz zz bb bb"""
        try:
            unpacked = struct.unpack(V2_STRUCT, payload[:TELEMETRY_PAYLOAD_LENGTH])

            version = unpacked[0]
            velocity_valid = unpacked[2] == 1
            gravity_velocity = unpacked[3] if velocity_valid else None
            temp_raw = unpacked[4]
            gravity_float = unpacked[5]
            accel_x_raw = unpacked[6]
            accel_y_raw = unpacked[7]
            accel_z_raw = unpacked[8]
            battery_raw = unpacked[9]

            # Convert using official RAPT formulas
            temperature = temp_raw / 128.0 - 273.15  # Kelvin to Celsius
            gravity = gravity_float / 1000.0
            battery = int(battery_raw / 256.0)
            accel_x = accel_x_raw / 16.0
            accel_y = accel_y_raw / 16.0
            accel_z = accel_z_raw / 16.0

            _LOGGER.debug("v2 - temp=%.2f°C, gravity=%.4f, battery=%d%%, velocity=%.4f (valid=%s), accel=(%.2f,%.2f,%.2f)",
                          temperature, gravity, battery, gravity_velocity or 0, velocity_valid, accel_x, accel_y, accel_z)

            return RAPTPillSensorData(
                temperature=temperature,
                gravity=gravity,
                gravity_velocity=gravity_velocity,
                gravity_velocity_valid=velocity_valid,
                battery=battery,
                accelerometer_x=accel_x,
                accelerometer_y=accel_y,
                accelerometer_z=accel_z,
                data_format_version=version,
            )

        except struct.error as e:
            _LOGGER.error("v2 struct unpack failed: %s", e)
            return None


class RAPTPillBluetoothDeviceData:
    """Tracks the latest data received from a RAPT Pill."""

    def __init__(self, device_name: str) -> None:
        """Initialize the device data tracker."""
        self.device_name = device_name
        self.parser = RAPTPillBLEParser()
        self._last_service_info: BluetoothServiceInfoBleak | None = None

    def handle_advertisement(self, service_info: BluetoothServiceInfoBleak) -> None:
        """Process a Bluetooth advertisement from the device."""
        self._last_service_info = service_info
        self.parser.parse_advertisement(service_info)

    @property
    def last_telemetry_at(self) -> datetime | None:
        """Return when telemetry was last parsed."""
        return self.parser.last_telemetry_at

    def get_last_sensor_data(self) -> RAPTPillSensorData | None:
        """Get the last parsed sensor data."""
        return self.parser.last_data

    def get_last_service_info(self) -> BluetoothServiceInfoBleak | None:
        """Get the last Bluetooth service info."""
        return self._last_service_info
