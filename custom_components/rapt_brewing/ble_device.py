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
    battery: int | None = None
    signal_strength: int | None = None
    accelerometer_x: float | None = None
    accelerometer_y: float | None = None
    accelerometer_z: float | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "temperature": self.temperature,
            "gravity": self.gravity,
            "battery": self.battery,
            "signal_strength": self.signal_strength,
            "accelerometer_x": self.accelerometer_x,
            "accelerometer_y": self.accelerometer_y,
            "accelerometer_z": self.accelerometer_z,
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
        if len(data) < 21:
            _LOGGER.warning("RAPT metrics data too short: %d bytes", len(data))
            return None
        
        try:
            # Parse according to the actual RAPT format (21 bytes minimum)
            # Based on rapt-ble library: ">BB6sHfhhhh" 
            # B = data type/version (1 byte)
            # B = flags or sequence (1 byte) 
            # 6s = device identifier (6 bytes)
            # H = sequence number (2 bytes)
            # f = temperature in Celsius (4 bytes)
            # h = gravity * 1000 (2 bytes)
            # h = battery level (2 bytes) 
            # h = accelerometer X (2 bytes)
            # h = accelerometer Y (2 bytes)
            
            _LOGGER.debug("Parsing RAPT data: %d bytes: %s", len(data), data.hex())
            
            # Use 21 bytes for the core format
            unpacked = struct.unpack(">BB6sHfhhhh", data[:21])
            
            data_type = unpacked[0]
            flags = unpacked[1]  
            device_id = unpacked[2]
            sequence = unpacked[3]
            temperature = unpacked[4]  # Already in Celsius
            gravity_raw = unpacked[5]
            battery_raw = unpacked[6]
            accel_x_raw = unpacked[7]
            accel_y_raw = unpacked[8]
            
            # Convert raw values to meaningful units
            gravity = gravity_raw / 1000.0 if gravity_raw != 0 else None
            battery = int(battery_raw) if battery_raw >= 0 else None
            accel_x = accel_x_raw / 16.0
            accel_y = accel_y_raw / 16.0
            accel_z = 0.0  # We only have X and Y in this format
            
            # Validate reasonable ranges
            if temperature < -50 or temperature > 100:
                _LOGGER.warning("Invalid temperature reading: %.2f°C", temperature)
                temperature = None
                
            if gravity and (gravity < 0.5 or gravity > 2.0):
                _LOGGER.warning("Invalid gravity reading: %.3f", gravity)
                gravity = None
                
            if battery and (battery < 0 or battery > 100):
                _LOGGER.warning("Invalid battery reading: %d%%", battery)
                battery = None
            
            sensor_data = RAPTPillSensorData(
                temperature=temperature,
                gravity=gravity,
                battery=battery,
                accelerometer_x=accel_x,
                accelerometer_y=accel_y,
                accelerometer_z=accel_z,
            )
            
            self._last_data = sensor_data
            
            _LOGGER.debug(
                "Parsed RAPT data - Temp: %.1f°C, Gravity: %.3f, Battery: %d%%, "
                "Accel: (%.2f, %.2f)",
                temperature or 0,
                gravity or 0,
                battery or 0,
                accel_x,
                accel_y,
            )
            
            return sensor_data
            
        except struct.error as e:
            _LOGGER.error("Failed to parse RAPT metrics data: %s", e)
            return None
        except Exception as e:
            _LOGGER.exception("Unexpected error parsing RAPT data: %s", e)
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
    
    def _async_handle_bluetooth_data_update(
        self, service_info: BluetoothServiceInfoBleak
    ) -> PassiveBluetoothDataUpdate:
        """Handle Bluetooth data updates."""
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