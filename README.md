# RAPT Brewing Session Manager

[![GitHub Release](https://img.shields.io/github/v/release/sbaird123/rapt-brewing-hacs?style=for-the-badge)](https://github.com/sbaird123/rapt-brewing-hacs/releases)
[![GitHub Activity](https://img.shields.io/github/commit-activity/y/sbaird123/rapt-brewing-hacs?style=for-the-badge)](https://github.com/sbaird123/rapt-brewing-hacs/commits/main)
[![License](https://img.shields.io/github/license/sbaird123/rapt-brewing-hacs?style=for-the-badge)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

A Home Assistant integration for monitoring brewing sessions with RAPT Pill hydrometers via Bluetooth.

## Features

### 🍺 Single Session Brewing Management
- **Simple Session Control**: Start new session, delete, and rename
- **Auto-Detection**: Automatically sets original gravity from first reading
- **Target Setting**: Set target gravity and temperature for calculations
- **Historical Data**: Stores all session data for analysis

### 📊 Advanced Brewing Calculations
- **Automatic ABV**: Real-time alcohol percentage calculation with temperature correction
- **Attenuation Tracking**: Monitor apparent attenuation percentage
- **Fermentation Rate**: Track gravity change over time (SG points per hour)
- **Temperature Correction**: Accurate gravity readings compensated for temperature

### 🔔 Smart Brewing Alerts
- **Stuck Fermentation**: Automatically detects when fermentation stalls
- **Temperature Monitoring**: High/low temperature warnings
- **Completion Detection**: Notification when target gravity is reached
- **Device Alerts**: Low battery and connectivity warnings

### 📈 Comprehensive Data Monitoring
- **20+ Sensors**: Complete brewing data coverage including accelerometer and fermentation activity
- **Real-time Updates**: Live gravity, temperature, and device status
- **BLE Integration**: Direct Bluetooth Low Energy communication with RAPT Pill
- **Dashboard Ready**: Complete Lovelace configuration included

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add repository URL: `https://github.com/sbaird123/rapt-brewing-hacs`
6. Select category: "Integration"
7. Click "Add"
8. Find "RAPT Brewing Session Manager" in HACS and install
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page][releases]
2. Extract the `rapt_brewing` folder to your `custom_components` directory
3. Restart Home Assistant

## Configuration

### Prerequisites
- Home Assistant version 2023.9.0 or later
- Bluetooth integration enabled in Home Assistant
- RAPT Pill hydrometer device
- ESPHome BLE proxy devices (recommended for better range and reliability)

### Setup Steps
1. **Enable Bluetooth** in Home Assistant (if not already enabled)
2. **Power on your RAPT Pill** and ensure it's in Bluetooth mode
3. Go to **Settings** → **Devices & Services** → **Add Integration**
4. Search for **"RAPT Brewing Session Manager"**
5. The integration will **automatically discover** your RAPT Pill via Bluetooth
6. Select your device from the list or enter manually if not found
7. Click **Submit** to complete setup

### Bluetooth Setup
- Ensure your RAPT Pill is powered on and transmitting
- The device should be within Bluetooth range of your Home Assistant instance
- If not automatically discovered, you can enter the device MAC address manually

## Usage

### Starting Your First Session
1. Use the "Start New Session" button (automatically stops any existing session)
2. Session automatically created with timestamp name (e.g., "Brew 2025-01-17 18:30")
3. Customize session name using the Session Name text input
4. Set brewing parameters using number inputs:
   - **Original Gravity**: Starting gravity (auto-detected from first reading)
   - **Target Gravity**: Expected final gravity
   - **Target Temperature**: Ideal fermentation temperature

### Monitoring Progress
- **Real-time Readings**: Current gravity, temperature, battery level
- **Calculated Metrics**: ABV%, attenuation%, fermentation rate
- **Historical Charts**: Gravity and temperature trends over time
- **Alert System**: Automatic alerts for stuck fermentation, temperature issues, and low battery

### Managing Sessions
- **Single Session Focus**: One active session at a time for simplicity
- **Session History**: Historical data stored for completed sessions
- **Session Naming**: Customize session names during brewing
- **Target Setting**: Set original gravity, target gravity, and target temperature

## Dashboard Configuration

Copy the contents of `dashboard_config.yaml` to create a comprehensive brewing dashboard:

```yaml
# Add to your Lovelace dashboard
title: RAPT Brewing Dashboard
cards:
  - type: entities
    title: Session Control
    entities:
      - text.rapt_brewing_session_name
      - sensor.rapt_brewing_session_state
      - button.rapt_brewing_start_session
      - button.rapt_brewing_delete_session
  # ... more configuration available in dashboard_config.yaml
```

## Available Sensors

### Core Brewing Sensors
| Sensor | Description | Unit |
|--------|-------------|------|
| `session_name` | Current session name | - |
| `original_gravity` | Starting gravity | SG |
| `current_gravity` | Current specific gravity (raw) | SG |
| `current_gravity_temp_corrected` | Temperature-corrected gravity | SG |
| `target_gravity` | Target final gravity | SG |
| `alcohol_percentage` | Calculated alcohol by volume | % |
| `attenuation` | Apparent attenuation | % |
| `fermentation_rate` | Gravity change rate | SG/hr |
| `current_temperature` | Current temperature | °C |
| `target_temperature` | Target fermentation temperature | °C |

### Device & Status Sensors
| Sensor | Description | Unit |
|--------|-------------|------|
| `battery_level` | RAPT Pill battery level | % |
| `signal_strength` | BLE signal strength | dBm |
| `session_duration` | Total session time | hours |
| `last_reading_time` | Last sensor reading timestamp | timestamp |
| `active_alerts` | Number of active alerts | count |

### Advanced Sensors
| Sensor | Description | Unit |
|--------|-------------|------|
| `gravity_velocity` | Official RAPT gravity velocity | SG/day |
| `accelerometer_x` | X-axis acceleration | g |
| `accelerometer_y` | Y-axis acceleration | g |
| `accelerometer_z` | Z-axis acceleration | g |
| `device_stability` | Device stability classification | - |
| `fermentation_activity` | Fermentation activity level | - |
| `firmware_version` | RAPT Pill firmware version | - |
| `device_type` | Device type information | - |
| `data_format_version` | BLE data format version | - |

## Available Controls

### Buttons
- **Start New Session**: Creates a new session (replaces any existing session)
- **Delete Current Session**: Removes the current session
- **Clear Alerts**: Acknowledges and clears active alerts

### Text Inputs
- **Session Name**: Edit the current session name

### Number Inputs
- **Original Gravity**: Set starting gravity (1.000-1.200 SG)
- **Target Gravity**: Set target final gravity (0.990-1.200 SG)
- **Target Temperature**: Set fermentation temperature (0-50°C)

## Alerts & Notifications

### Alert Types
- **Stuck Fermentation**: No gravity change for 48+ hours
- **Temperature High**: Above 30°C (86°F)
- **Temperature Low**: Below 10°C (50°F)
- **Fermentation Complete**: Target gravity reached
- **Low Battery**: Below 20%

### Notification Configuration
Alerts automatically create Home Assistant persistent notifications. Configure additional notification platforms in `configuration.yaml`:

```yaml
notify:
  - name: brewing_alerts
    platform: telegram  # or pushbullet, email, etc.
    chat_id: YOUR_CHAT_ID
    api_key: YOUR_API_KEY
```

## Troubleshooting

### Common Issues

**Integration won't load**
- Verify Bluetooth is enabled on your Home Assistant server
- Check that your RAPT Pill is broadcasting (manufacturer IDs 16722 or 17739)
- Review Home Assistant logs for errors

**No data updates**
- Ensure RAPT Pill is connected and transmitting
- Check Bluetooth connectivity and range (ESPHome BLE proxies recommended)
- Verify integration is receiving BLE advertisements in logs

**Incorrect calculations**
- Confirm original gravity is set correctly
- Check target gravity values
- Ensure sufficient data points for rate calculations

### Debug Logging
Add to `configuration.yaml`:
```yaml
logger:
  logs:
    custom_components.rapt_brewing: debug
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

- **Issues**: [GitHub Issues][issues]
- **Discussions**: [GitHub Discussions][discussions]
- **Home Assistant Community**: [Community Forum][community]

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [RAPT (KegLand)](https://rapt.io) for excellent brewing hardware
- Home Assistant community for integration support
- All contributors and beta testers

---

**Issues & Support:**
- [GitHub Issues](https://github.com/sbaird123/rapt-brewing-hacs/issues)
- [GitHub Discussions](https://github.com/sbaird123/rapt-brewing-hacs/discussions)
- [Home Assistant Community](https://community.home-assistant.io/)