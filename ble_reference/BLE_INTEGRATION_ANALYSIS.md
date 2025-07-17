# RAPT BLE Integration Analysis

This document provides a comprehensive analysis of the RAPT BLE integration source code for integration into the RAPT Brewing Session Manager.

## Key Files Retrieved

### Home Assistant RAPT BLE Integration
- `homeassistant_rapt_ble_init.py` - Main integration setup
- `homeassistant_rapt_ble_const.py` - Constants
- `homeassistant_rapt_ble_sensor.py` - Sensor platform implementation
- `homeassistant_rapt_ble_config_flow.py` - Configuration flow
- `homeassistant_rapt_ble_manifest.json` - Integration manifest

### RAPT-BLE Python Package
- `rapt_ble_init.py` - Package initialization
- `rapt_ble_parser.py` - Core BLE parsing logic

## Critical BLE Data

### Bluetooth Manufacturer IDs
- **16722** (0x4152) - Main data payload (prefix "RA" from "RAPT")
- **17739** (0x454B) - Version information (prefix "KE" from "KEG")

### Data Structure Analysis

#### Advertisement Payload Structure
The RAPT Pill sends two types of BLE advertisements:

1. **Metrics Data (Manufacturer ID 16722)**:
   - 23-byte payload
   - Big-endian format
   - Contains: version, MAC (v1 only), temperature, gravity, accelerometer (x,y,z), battery

2. **Version Data (Manufacturer ID 17739)**:
   - Variable length
   - Contains software version string
   - Format: "KEG{version_string}"

#### Version 1 Payload (23 bytes):
```c
typedef struct __attribute__((packed)) {
    char prefix[4];        // "RAPT"
    uint8_t version;       // 0x01
    uint8_t mac[6];        // Device MAC address
    uint16_t temperature;  // Raw temp / 128 - 273.15
    float gravity;         // Raw gravity / 1000
    int16_t x;             // Accel X / 16
    int16_t y;             // Accel Y / 16
    int16_t z;             // Accel Z / 16
    int16_t battery;       // Battery / 256
} RAPTPillMetricsV1;
```

#### Version 2 Payload (23 bytes):
```c
typedef struct __attribute__((packed)) {
    char prefix[4];              // "RAPT"
    uint8_t version;             // 0x02
    bool gravity_velocity_valid; // Velocity data validity
    float gravity_velocity;      // Gravity velocity
    uint16_t temperature;        // Raw temp / 128 - 273.15
    float gravity;               // Raw gravity / 1000
    int16_t x;                   // Accel X / 16
    int16_t y;                   // Accel Y / 16
    int16_t z;                   // Accel Z / 16
    int16_t battery;             // Battery / 256
} RAPTPillMetricsV2;
```

### Data Parsing Logic

#### Binary Unpacking
```python
# Unpack format: ">B6sHfhhhh" (big-endian)
# B = unsigned char (version)
# 6s = 6-byte string (MAC address, v1 only)
# H = unsigned short (temperature)
# f = float (gravity)
# h = short (x accelerometer)
# h = short (y accelerometer)
# h = short (z accelerometer)
# h = short (battery)
```

#### Value Conversions
- **Temperature**: `(raw_value / 128) - 273.15` (Celsius)
- **Gravity**: `raw_value / 1000` (specific gravity)
- **Accelerometer**: `raw_value / 16` (g-force)
- **Battery**: `raw_value / 256` (percentage)

## PassiveBluetoothProcessorCoordinator Pattern

### Key Components

1. **PassiveBluetoothProcessorCoordinator**:
   - Coordinates BLE scanning and data processing
   - Uses `BluetoothScanningMode.ACTIVE` for RAPT devices
   - Calls update method on BLE advertisement reception

2. **RAPTPillBluetoothDeviceData**:
   - Extends `BluetoothData` from `bluetooth_sensor_state_data`
   - Implements `_start_update()` method for BLE processing
   - Handles manufacturer data filtering and parsing

3. **Device Detection Logic**:
   - Filters by manufacturer IDs 16722 and 17739
   - Validates payload length (23 bytes for metrics)
   - Ignores hardware revision advertisements ("PTdPillG1")

### Integration Pattern

```python
# Setup coordinator
data = RAPTPillBluetoothDeviceData()
coordinator = PassiveBluetoothProcessorCoordinator(
    hass,
    logger,
    address=device_address,
    mode=BluetoothScanningMode.ACTIVE,
    update_method=data.update,
)

# Start scanning
coordinator.async_start()
```

## Sensor Entity Mapping

### Available Sensors
- **Temperature**: Celsius, measurement class
- **Specific Gravity**: Unitless, measurement class
- **Battery**: Percentage, diagnostic category
- **Signal Strength**: dBm, diagnostic category (disabled by default)

### Entity Descriptions
```python
SENSOR_DESCRIPTIONS = {
    (DeviceClass.TEMPERATURE, Units.TEMP_CELSIUS): SensorEntityDescription(
        key=f"{DeviceClass.TEMPERATURE}_{Units.TEMP_CELSIUS}",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # ... other sensors
}
```

## Dependencies Required

### Python Packages
- `bluetooth-data-tools` - Bluetooth utility functions
- `bluetooth-sensor-state-data` - Base classes for BLE sensors
- `home-assistant-bluetooth` - HA Bluetooth integration
- `sensor-state-data` - Sensor data structures

### Home Assistant Components
- `homeassistant.components.bluetooth` - Core Bluetooth support
- `homeassistant.components.bluetooth.passive_update_processor` - BLE coordination

## Integration Strategy for RAPT Brewing

### Option 1: Direct Integration
Copy the core parsing logic from `rapt_ble_parser.py` into your integration:
- Extract `RAPTPillBluetoothDeviceData` class
- Adapt manufacturer ID filtering
- Integrate with existing coordinator pattern

### Option 2: Embedded Parser
Create a minimal embedded version:
- Extract only the binary parsing logic
- Implement custom BLE scanning within existing framework
- Adapt data structures to match RAPT Brewing entities

### Recommended Approach
1. **Extract Core Parser**: Copy `_process_metrics()` and `_process_version()` methods
2. **Adapt Data Flow**: Integrate with existing `RAPTCoordinator`
3. **Entity Mapping**: Map parsed data to existing RAPT Brewing sensor entities
4. **Config Integration**: Add BLE device discovery to existing config flow

## Code Snippets for Integration

### Minimal Parser Implementation
```python
import struct
from binascii import hexlify

class RAPTPillBLEParser:
    """Minimal RAPT Pill BLE parser for direct integration."""
    
    @staticmethod
    def parse_metrics(data: bytes) -> dict:
        """Parse RAPT Pill metrics from BLE advertisement."""
        if len(data) != 23:
            return None
            
        # Unpack: version, mac, temp, gravity, x, y, z, battery
        raw = struct.unpack(">B6sHfhhhh", data[2:])
        
        return {
            "version": raw[0],
            "mac": hexlify(raw[1]).decode("ascii") if raw[0] == 1 else "",
            "temperature": round(raw[2] / 128 - 273.15, 2),
            "gravity": round(raw[3] / 1000, 4),
            "battery": round(raw[7] / 256),
            "accelerometer": {
                "x": raw[4] / 16,
                "y": raw[5] / 16,
                "z": raw[6] / 16,
            }
        }
```

### BLE Integration Hook
```python
def process_ble_advertisement(self, service_info):
    """Process BLE advertisement from RAPT Pill."""
    manufacturer_data = service_info.manufacturer_data
    
    # Check for RAPT manufacturer IDs
    if 16722 in manufacturer_data:
        data = manufacturer_data[16722]
        if len(data) == 23 and data != b"PTdPillG1":
            metrics = RAPTPillBLEParser.parse_metrics(data)
            if metrics:
                self.update_device_data(service_info.address, metrics)
```

This analysis provides all the necessary information to integrate RAPT Pill BLE functionality directly into your RAPT Brewing Session Manager integration.