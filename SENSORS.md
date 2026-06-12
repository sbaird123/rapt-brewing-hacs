# RAPT Brewing - Complete Entity List

## Core Brewing Sensors
| Sensor | Description | Unit |
|--------|-------------|------|
| `session_name` | Current session name | - |
| `original_gravity` | Starting gravity | SG or °P |
| `current_gravity` | Current specific gravity (raw) | SG or °P |
| `current_gravity_temp_corrected` | Temperature-corrected gravity | SG or °P |
| `target_gravity` | Target final gravity | SG or °P |
| `alcohol_percentage` | Calculated alcohol by volume | % |
| `attenuation` | Apparent attenuation | % |
| `fermentation_rate` | Gravity change rate (uses official RAPT gravity velocity when available) | SG/hr |
| `current_temperature` | Current temperature | °C |
| `target_temperature` | Target fermentation temperature | °C |

Gravity sensors display in SG by default; switch to degrees Plato under
**Configure → Display & calibration**.

## Device & Status Sensors
| Sensor | Description | Unit |
|--------|-------------|------|
| `battery_level` | RAPT Pill battery level | % |
| `signal_strength` | BLE signal strength | dBm |
| `session_duration` | Total session time | hours |
| `last_reading_time` | Last sensor reading timestamp | timestamp |
| `active_alerts` | Number of active alerts | count |

## Advanced Sensors
| Sensor | Description | Unit |
|--------|-------------|------|
| `gravity_velocity` | Official RAPT gravity velocity (v2 firmware) | points/day |
| `accelerometer_x` | X-axis acceleration | g |
| `accelerometer_y` | Y-axis acceleration | g |
| `accelerometer_z` | Z-axis acceleration | g |
| `device_stability` | Device stability classification | - |
| `fermentation_activity` | Fermentation activity level | - |
| `firmware_version` | RAPT Pill firmware version | - |
| `device_type` | Device type information | - |
| `data_format_version` | BLE data format version | - |

Live device readings (gravity, temperature, battery, accelerometer, etc.)
become **unavailable** when the device is offline, so a dead battery doesn't
masquerade as a stable fermentation.

## Binary Sensors
| Sensor | Description |
|--------|-------------|
| `device_online` | Connectivity — on while fresh data arrives within the offline timeout (configurable) |

## Controls
| Entity | Type | Description |
|--------|------|-------------|
| `start_session` | button | Start a new session (auto-stops any active one) |
| `stop_session` | button | Stop the current session |
| `delete_session` | button | Delete the current session |
| `clear_alerts` | button | Acknowledge all alerts |
| `session` | select | Browse session history — switch which session the sensors display |
| `session_name` | text | Rename the current session |
| `target_gravity` / `original_gravity` / `target_temperature` | number | Session parameters (always SG / °C) |

## Services
| Service | Description |
|---------|-------------|
| `rapt_brewing.start_session` | Start a named session with optional recipe, OG, target gravity/temperature |
| `rapt_brewing.stop_session` | Stop the current session |
| `rapt_brewing.add_session_note` | Append a timestamped note to the current session |

All services accept an optional `device_id` to target a specific entry when
multiple RAPT devices are configured.

## Events

Every alert fires a `rapt_brewing_alert` event on the Home Assistant bus with
`alert_type`, `message`, `session_id`, `session_name`, and `entry_id` —
useful for automations (e.g. turn on the glycol chiller on `temperature_high`).

## Entity Naming

All entities are prefixed with the device name in Home Assistant, e.g.:
- `sensor.rapt_brewing_session_manager_current_gravity`
- `sensor.rapt_brewing_session_manager_alcohol_percentage`
- `binary_sensor.rapt_brewing_session_manager_device_online`
