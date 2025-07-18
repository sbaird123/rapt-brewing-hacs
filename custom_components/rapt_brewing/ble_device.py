"""BLE device handler for RAPT Pill integration."""
from __future__ import annotations

import logging
import struct
from dataclasses import dataclass
from typing import Any

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# RAPT Pill Bluetooth manufacturer IDs
RAPT_MANUFACTURER_ID = 16722  # 0x4152 - "RA" from RAPT
KEGLAND_MANUFACTURER_ID = 17739  # 0x454B - "KE" from KEG

# Data start patterns for manufacturer data
RAPT_DATA_START = [80, 84]  # "PT" - Pill Telemetry
KEGLAND_DATA_START = [71]   # "G" - General/Version


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
        self._last_data: RAPTPillSensorData | None = None
    
    def parse_advertisement(
        self, service_info: BluetoothServiceInfoBleak
    ) -> RAPTPillSensorData | None:
        """Parse BLE advertisement data."""
        manufacturer_data = service_info.manufacturer_data
        
        
        # Check for RAPT manufacturer data
        if RAPT_MANUFACTURER_ID in manufacturer_data:
            data = manufacturer_data[RAPT_MANUFACTURER_ID]
            if len(data) >= 2 and list(data[:2]) == RAPT_DATA_START:
                return self._parse_metrics_data(data)
        
        # Check for KegLand manufacturer data  
        if KEGLAND_MANUFACTURER_ID in manufacturer_data:
            data = manufacturer_data[KEGLAND_MANUFACTURER_ID]
            if len(data) >= 1 and data[0] == KEGLAND_DATA_START[0]:
                # Version data - not used for sensor values
                _LOGGER.debug("Received KegLand version data")
        
        return self._last_data
    
    def _parse_metrics_data(self, data: bytes) -> RAPTPillSensorData | None:
        """Parse metrics data from RAPT manufacturer data."""
        if len(data) < 4:
            _LOGGER.warning("RAPT data too short: %d bytes", len(data))
            return None
        
        try:
            _LOGGER.debug("Parsing RAPT data: %d bytes: %s", len(data), data.hex())
            
            # Check for different packet types based on prefix
            if data[:4] == b'RAPT':
                return self._parse_rapt_telemetry(data)
            elif data[:3] == b'KEG':
                return self._parse_keg_firmware(data)
            elif data[:2] == b'PT':
                return self._parse_legacy_format(data)
            else:
                _LOGGER.warning("Unknown RAPT packet format: %s", data[:4].hex())
                return None
                
        except Exception as e:
            _LOGGER.error("Error parsing RAPT data: %s", e)
            return None
    
    def _parse_rapt_telemetry(self, data: bytes) -> RAPTPillSensorData | None:
        """Parse RAPT telemetry data (v1 and v2 formats)."""
        if len(data) < 26:  # Minimum for v1 format
            _LOGGER.warning("RAPT telemetry data too short: %d bytes", len(data))
            return None
        
        try:
            # Skip "RAPT" prefix (4 bytes)
            payload = data[4:]
            
            # Get format version
            format_version = payload[0]
            _LOGGER.debug("RAPT format version: %d", format_version)
            
            if format_version == 1:
                return self._parse_v1_format(payload)
            elif format_version == 2:
                return self._parse_v2_format(payload)
            else:
                _LOGGER.warning("Unknown RAPT format version: %d", format_version)
                return None
                
        except Exception as e:
            _LOGGER.error("Error parsing RAPT telemetry: %s", e)
            return None
    
    def _parse_v1_format(self, payload: bytes) -> RAPTPillSensorData | None:
        """Parse v1 format: 0x01 mm mm mm mm mm mm tt tt gg gg gg gg xx xx yy yy zz zz bb bb"""
        if len(payload) < 21:
            _LOGGER.warning("v1 payload too short: %d bytes", len(payload))
            return None
        
        try:
            # v1 format: B6sHfhhhh (version + MAC + temp + gravity + accel_x + accel_y + accel_z + battery)
            unpacked = struct.unpack(">B6sHfhhhh", payload[:21])
            
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
                data_format_version=version
            )
            
        except struct.error as e:
            _LOGGER.error("v1 struct unpack failed: %s", e)
            return None
    
    def _parse_v2_format(self, payload: bytes) -> RAPTPillSensorData | None:
        """Parse v2 format: 0x02 0x00 cc vv vv vv vv tt tt gg gg gg gg xx xx yy yy zz zz bb bb"""
        if len(payload) < 23:
            _LOGGER.warning("v2 payload too short: %d bytes", len(payload))
            return None
        
        try:
            # v2 format: BB B f H f hhhh (version + reserved + velocity_valid + velocity + temp + gravity + accel_x + accel_y + accel_z + battery)
            unpacked = struct.unpack(">BBBfHfhhhh", payload[:23])
            
            version = unpacked[0]
            reserved = unpacked[1]  # Should be 0x00
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
            
            # For v2, calculate MAC from BLE address (subtract 2 from last octet)
            # This would need to be done in the caller since we don't have BLE address here
            
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
                data_format_version=version
            )
            
        except struct.error as e:
            _LOGGER.error("v2 struct unpack failed: %s", e)
            return None
    
    def _parse_keg_firmware(self, data: bytes) -> RAPTPillSensorData | None:
        """Parse KEG firmware version packet: 0x4b 0x45 0x47 <firmware version string>"""
        if len(data) < 4:
            return None
        
        try:
            # Skip "KEG" prefix (3 bytes)
            firmware_version = data[3:].decode('utf-8', errors='ignore').strip()
            _LOGGER.debug("Firmware version: %s", firmware_version)
            
            return RAPTPillSensorData(firmware_version=firmware_version)
            
        except Exception as e:
            _LOGGER.error("Error parsing firmware version: %s", e)
            return None
    
    def _parse_device_type(self, data: bytes) -> RAPTPillSensorData | None:
        """Parse device type packet: 0x52 0x41 0x50 0x54 0x64 <device type string>"""
        if len(data) < 6:
            return None
        
        try:
            # Skip "RAPT" + 0x64 prefix (5 bytes)
            device_type = data[5:].decode('utf-8', errors='ignore').strip()
            _LOGGER.debug("Device type: %s", device_type)
            
            return RAPTPillSensorData(device_type=device_type)
            
        except Exception as e:
            _LOGGER.error("Error parsing device type: %s", e)
            return None
    
    def _parse_legacy_format(self, data: bytes) -> RAPTPillSensorData | None:
        """Parse legacy format for backwards compatibility."""
        if len(data) < 23:
            _LOGGER.warning("Legacy format data too short: %d bytes", len(data))
            return None
        
        try:
            # Skip "PT" prefix and use old parsing logic
            payload = data[2:]
            
            if len(payload) >= 21:
                unpacked = struct.unpack(">B6sHfhhhh", payload[:21])
                
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
                
                _LOGGER.debug("Legacy - temp=%.2f°C, gravity=%.4f, battery=%d%%", 
                             temperature, gravity, battery)
                
                return RAPTPillSensorData(
                    temperature=temperature,
                    gravity=gravity,
                    battery=battery,
                    accelerometer_x=accel_x,
                    accelerometer_y=accel_y,
                    accelerometer_z=accel_z,
                    data_format_version=version
                )
            else:
                _LOGGER.warning("Legacy payload too short: %d bytes", len(payload))
                return None
                
        except struct.error as e:
            _LOGGER.error("Legacy struct unpack failed: %s", e)
            return None


class RAPTPillBluetoothDeviceData(PassiveBluetoothDataProcessor):
    """Data processor for RAPT Pill Bluetooth devices."""
    
    def __init__(self, hass: HomeAssistant, device_name: str) -> None:
        """Initialize the data processor."""
        super().__init__(update_method=self._async_handle_bluetooth_data_update)
        self.hass = hass
        self.device_name = device_name
        self.parser = RAPTPillBLEParser()
        self._last_service_info: BluetoothServiceInfoBleak | None = None
        
        # Log that the BLE device processor was created
        _LOGGER.warning("RAPT BLE DEVICE PROCESSOR CREATED for device: %s", device_name)
    
    def _async_handle_bluetooth_data_update(
        self, service_info: BluetoothServiceInfoBleak
    ) -> PassiveBluetoothDataUpdate:
        """Handle Bluetooth data updates."""
        # Log every BLE update we receive - GUARANTEED WARNING LOG
        _LOGGER.warning("!!! RAPT BLE UPDATE RECEIVED !!! Device: %s, Manufacturers: %s", 
                       service_info.address, list(service_info.manufacturer_data.keys()))
        
        self._last_service_info = service_info
        
        # Filter to only RAPT devices since we can't use matcher parameter
        manufacturer_data = service_info.manufacturer_data
        is_rapt_device = (
            RAPT_MANUFACTURER_ID in manufacturer_data or
            KEGLAND_MANUFACTURER_ID in manufacturer_data
        )
        
        if not is_rapt_device:
            # Return empty update for non-RAPT devices
            return PassiveBluetoothDataUpdate(
                devices={},
                entity_descriptions={},
                entity_names={},
                entity_data={},
            )
        
        # Parse sensor data
        sensor_data = self.parser.parse_advertisement(service_info)
        
        if not sensor_data:
            # Return empty update if no valid data
            return PassiveBluetoothDataUpdate(
                devices={},
                entity_descriptions={},
                entity_names={},
                entity_data={},
            )
        
        # Signal strength from service info
        signal_strength = service_info.rssi
        
        # Create device identifier
        device_id = service_info.address
        
        # Create entity data updates
        entity_data = {}
        entity_descriptions = {}
        entity_names = {}
        
        # Temperature sensor
        if sensor_data.temperature is not None:
            key = PassiveBluetoothEntityKey(device_id, "temperature")
            entity_data[key] = sensor_data.temperature
            entity_descriptions[key] = {
                "device_class": "temperature",
                "native_unit_of_measurement": "°C",
                "state_class": "measurement",
            }
            entity_names[key] = f"{self.device_name} Temperature"
        
        # Gravity sensor
        if sensor_data.gravity is not None:
            key = PassiveBluetoothEntityKey(device_id, "gravity")
            entity_data[key] = sensor_data.gravity
            entity_descriptions[key] = {
                "icon": "mdi:speedometer",
                "state_class": "measurement",
            }
            entity_names[key] = f"{self.device_name} Gravity"
        
        # Battery sensor
        if sensor_data.battery is not None:
            key = PassiveBluetoothEntityKey(device_id, "battery")
            entity_data[key] = sensor_data.battery
            entity_descriptions[key] = {
                "device_class": "battery",
                "native_unit_of_measurement": "%",
                "state_class": "measurement",
            }
            entity_names[key] = f"{self.device_name} Battery"
        
        # Signal strength sensor
        key = PassiveBluetoothEntityKey(device_id, "signal_strength")
        entity_data[key] = signal_strength
        entity_descriptions[key] = {
            "device_class": "signal_strength",
            "native_unit_of_measurement": "dBm",
            "state_class": "measurement",
        }
        entity_names[key] = f"{self.device_name} Signal Strength"
        
        # Device information
        devices = {
            device_id: {
                "name": self.device_name,
                "model": "RAPT Pill",
                "manufacturer": "KegLand",
                "sw_version": None,  # Could be extracted from version data
                "hw_version": None,
            }
        }
        
        return PassiveBluetoothDataUpdate(
            devices=devices,
            entity_descriptions=entity_descriptions,
            entity_names=entity_names,
            entity_data=entity_data,
        )
    
    def get_last_sensor_data(self) -> RAPTPillSensorData | None:
        """Get the last parsed sensor data."""
        return self.parser._last_data
    
    def get_last_service_info(self) -> BluetoothServiceInfoBleak | None:
        """Get the last Bluetooth service info."""
        return self._last_service_info