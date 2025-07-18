# RAPT Brewing Session Manager

[![GitHub Release](https://img.shields.io/github/v/release/sbaird123/rapt-brewing-hacs?style=for-the-badge)](https://github.com/sbaird123/rapt-brewing-hacs/releases)
[![GitHub Activity](https://img.shields.io/github/commit-activity/y/sbaird123/rapt-brewing-hacs?style=for-the-badge)](https://github.com/sbaird123/rapt-brewing-hacs/commits/main)
[![License](https://img.shields.io/github/license/sbaird123/rapt-brewing-hacs?style=for-the-badge)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

A Home Assistant integration for monitoring brewing sessions with RAPT Pill hydrometers via Bluetooth.

![RAPT Brewing Dashboard](docs/dashboard-screenshot.png)

*Live dashboard showing a low-alcohol beer fermentation in progress with real-time gravity, temperature, and fermentation metrics. Optimized for both desktop and mobile devices.*

## Features

### 🍺 Brewing Session Monitoring
- **Simple Session Control**: Start new session, delete, and rename
- **Auto-Detection**: Automatically sets original gravity from first reading
- **Target Setting**: Set target gravity and temperature for calculations

### 📊 Advanced Brewing Calculations
- **Automatic ABV**: Real-time alcohol percentage calculation with temperature correction
- **Attenuation Tracking**: Monitor apparent attenuation percentage
- **Fermentation Rate**: Track gravity change over time (SG points per hour)
- **Temperature Correction**: Accurate gravity readings compensated for temperature

### 🔔 Smart Brewing Alerts
- **Stuck Fermentation**: Automatically detects when fermentation stalls
- **Temperature Monitoring**: High/low temperature warnings
- **Completion Detection**: Notification when target gravity is reached
- **Low Battery**: Alerts when RAPT Pill battery drops below 20%

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

### Session Controls
- **Single Session Focus**: One active session at a time for simplicity
- **Session Naming**: Customize session names during brewing
- **Target Setting**: Set original gravity, target gravity, and target temperature

## Dashboard Configuration

The integration provides a comprehensive brewing dashboard with real-time monitoring:

The dashboard shows:
- **Session Control**: Start/stop sessions, edit names, and delete sessions
- **Gravity Readings**: Raw and temperature-corrected gravity values
- **Temperature Monitoring**: Current and target temperatures
- **Fermentation Progress**: Alcohol percentage, attenuation, and fermentation activity
- **Device Status**: Battery level, signal strength, and connection status
- **Alerts**: Active alerts with clear button
- **Historical Charts**: Gravity trends over time showing fermentation progress

### Setup Instructions

**📱 [Desktop Dashboard →](dashboard_config.yaml)** | **📱 [Mobile Dashboard →](dashboard_config_mobile.yaml)**

1. Choose your layout and open the appropriate YAML file
2. Copy the complete YAML configuration
3. In Home Assistant: **Settings** → **Dashboards** → **Your Dashboard**
4. Click **Edit Dashboard** → **Add Card** → **Manual**
5. Paste the YAML and click **Save**

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

## Alerts & Notifications

### Alert Types
- **Stuck Fermentation**: No gravity change for 48+ hours
- **Temperature High**: Above 30°C (86°F)
- **Temperature Low**: Below 10°C (50°F)
- **Fermentation Complete**: Target gravity reached
- **Low Battery**: Below 20%

### Notification Configuration
Alerts automatically create Home Assistant persistent notifications in the UI. For external notifications:

#### ✅ Built-in Notification Service (Recommended - Easy!)
First, ensure you have a notification service configured (mobile app, Telegram, email, etc.). Then:

1. Go to **Settings** → **Devices & Services** → **RAPT Brewing Session Manager**
2. Click **Configure**
3. Select your notification service from the dropdown (e.g., `notify.mobile_app_your_phone`)
4. Click **Submit**

**Done!** The integration automatically sends alerts to your chosen notification service with rich data including alert type, session name, and brewing status.

## Troubleshooting

### Common Issues

**Integration won't load**
- Verify Bluetooth is enabled on your Home Assistant server
- Check that your RAPT Pill is broadcasting (manufacturer IDs 16722 or 17739)
- Review Home Assistant logs for errors

**No data updates**
- Ensure RAPT Pill is powered on and broadcasting BLE advertisements
- Check Bluetooth range (ESPHome BLE proxies recommended for better range)
- Verify integration is receiving BLE advertisements in logs

**Incorrect calculations**
- Confirm original gravity is set correctly
- Check target gravity values
- Ensure sufficient data points for rate calculations

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Issues & Support:**
- [GitHub Issues](https://github.com/sbaird123/rapt-brewing-hacs/issues)
- [GitHub Discussions](https://github.com/sbaird123/rapt-brewing-hacs/discussions)
- [Home Assistant Community](https://community.home-assistant.io/)