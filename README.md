# RAPT Brewing Session Manager

[![GitHub Release](https://img.shields.io/github/v/release/sbaird123/rapt-brewing-hacs?style=for-the-badge)](https://github.com/sbaird123/rapt-brewing-hacs/releases)
[![GitHub Activity](https://img.shields.io/github/commit-activity/y/sbaird123/rapt-brewing-hacs?style=for-the-badge)](https://github.com/sbaird123/rapt-brewing-hacs/commits/main)
[![License](https://img.shields.io/github/license/sbaird123/rapt-brewing-hacs?style=for-the-badge)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

A comprehensive Home Assistant integration for managing brewing sessions with RAPT Pill hydrometers.

## Features

### 🍺 Complete Brewing Session Management
- **Session Control**: Start, stop, pause, and resume brewing sessions
- **Multi-Session Support**: Track multiple brewing sessions with historical data
- **Stage Management**: Progress through fermentation stages (primary → secondary → conditioning → packaging)
- **Recipe Integration**: Track recipe names and brewing parameters

### 📊 Advanced Brewing Calculations
- **Automatic ABV**: Real-time alcohol percentage calculation using `(OG - FG) × 131.25`
- **Attenuation Tracking**: Monitor apparent attenuation percentage
- **Fermentation Rate**: Track gravity change over time (SG points per hour)
- **Progress Monitoring**: Visual progress indicators and trend analysis

### 🔔 Smart Brewing Alerts
- **Stuck Fermentation**: Automatically detects when fermentation stalls
- **Temperature Monitoring**: High/low temperature warnings
- **Completion Detection**: Notification when target gravity is reached
- **Device Alerts**: Low battery and connectivity warnings

### 📈 Rich Data Monitoring
- **16 Comprehensive Sensors**: Complete brewing data coverage
- **Real-time Updates**: Live gravity, temperature, and device status
- **Historical Analysis**: Long-term data storage and trend analysis
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
1. Use the "Start Brewing Session" button or service
2. Provide session details:
   - **Session Name**: e.g., "IPA Batch #1"
   - **Recipe** (optional): Recipe name or description
   - **Original Gravity**: Starting gravity reading
   - **Target Gravity**: Expected final gravity
   - **Target Temperature**: Ideal fermentation temperature

### Monitoring Progress
- **Real-time Readings**: Current gravity, temperature, battery level
- **Calculated Metrics**: ABV%, attenuation%, fermentation rate
- **Historical Charts**: Gravity and temperature trends over time
- **Stage Management**: Update fermentation stage as brewing progresses

### Managing Sessions
- **Session Control**: Start, stop, pause, resume operations
- **Multi-Session**: Switch between active sessions
- **Notes**: Add brewing notes throughout the process
- **Export**: Download session data for analysis

## Dashboard Configuration

Copy the contents of `dashboard_config.yaml` to create a comprehensive brewing dashboard:

```yaml
# Add to your Lovelace dashboard
title: RAPT Brewing Dashboard
cards:
  - type: entities
    title: Session Control
    entities:
      - sensor.rapt_brewing_session_name
      - sensor.rapt_brewing_session_state
      - button.rapt_brewing_start_session
      - button.rapt_brewing_stop_session
  # ... more configuration available in dashboard_config.yaml
```

## Available Sensors

| Sensor | Description | Unit |
|--------|-------------|------|
| `session_name` | Current session name | - |
| `session_state` | Session state (active/paused/completed) | - |
| `current_gravity` | Current specific gravity | SG |
| `alcohol_percentage` | Calculated alcohol by volume | % |
| `attenuation` | Apparent attenuation | % |
| `fermentation_rate` | Gravity change rate | SG/hr |
| `current_temperature` | Current temperature | °C |
| `battery_level` | RAPT Pill battery level | % |
| `session_duration` | Total session time | hours |
| `active_alerts` | Number of active alerts | count |

## Available Services

### `rapt_brewing.start_brewing_session`
Start a new brewing session with specified parameters.

```yaml
service: rapt_brewing.start_brewing_session
data:
  session_name: "IPA Batch #1"
  recipe: "Cascade Single Hop IPA"
  original_gravity: 1.050
  target_gravity: 1.010
  target_temperature: 18.0
```

### `rapt_brewing.stop_brewing_session`
Stop the current brewing session.

### `rapt_brewing.add_session_note`
Add a note to the current session.

```yaml
service: rapt_brewing.add_session_note
data:
  note: "Added dry hops - 50g Cascade"
```

### `rapt_brewing.export_session_data`
Export session data for analysis.

```yaml
service: rapt_brewing.export_session_data
data:
  format: "csv"  # or "json"
```

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
- Verify RAPT BLE integration is installed and working
- Check that device ID is correct
- Review Home Assistant logs for errors

**No data updates**
- Ensure RAPT Pill is connected and transmitting
- Check Bluetooth connectivity and range
- Verify BLE integration is receiving data

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