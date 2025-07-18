# RAPT Brewing Session Manager

[![GitHub Release](https://img.shields.io/github/v/release/sbaird123/rapt-brewing-hacs?style=for-the-badge)](https://github.com/sbaird123/rapt-brewing-hacs/releases)
[![GitHub Activity](https://img.shields.io/github/commit-activity/y/sbaird123/rapt-brewing-hacs?style=for-the-badge)](https://github.com/sbaird123/rapt-brewing-hacs/commits/main)
[![License](https://img.shields.io/github/license/sbaird123/rapt-brewing-hacs?style=for-the-badge)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

A Home Assistant integration for monitoring brewing sessions with RAPT Pill hydrometers via Bluetooth.

![RAPT Brewing Dashboard](docs/dashboard-screenshot.png)

*Live dashboard showing a low-alcohol beer fermentation in progress with real-time gravity, temperature, and fermentation metrics. Optimized for both desktop and mobile devices.*

## Features

- **🍺 Session Monitoring**: Start/stop sessions with auto-detection of original gravity
- **📊 Advanced Calculations**: Real-time ABV, attenuation, fermentation rate with temperature correction
- **🔔 Smart Alerts**: Stuck fermentation, temperature warnings, completion detection, low battery
- **📈 Comprehensive Data**: 20+ sensors including accelerometer and fermentation activity
- **📱 Dashboard Ready**: Complete mobile and desktop Lovelace configurations

## Installation

### HACS (Recommended)
1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/sbaird123/rapt-brewing-hacs` as Integration
3. Install "RAPT Brewing Session Manager" and restart Home Assistant

### Manual Installation
1. Download latest release and extract `rapt_brewing` folder to `custom_components`
2. Restart Home Assistant

## Configuration

**Requirements:** Home Assistant 2023.9.0+, Bluetooth enabled, RAPT Pill device

**Setup:** Settings → Devices & Services → Add Integration → Search "RAPT Brewing Session Manager" → Select your device → Submit

## Usage

1. **Start Session**: Click "Start New Session" button (auto-creates timestamp name)
2. **Set Parameters**: Original gravity (auto-detected), target gravity, target temperature
3. **Monitor**: Real-time gravity, temperature, ABV%, attenuation%, fermentation rate
4. **Alerts**: Automatic notifications for stuck fermentation, temperature issues, low battery

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

**Core Brewing:** Session name, original/current/target gravity (with temperature correction), alcohol %, attenuation %, fermentation rate, temperature

**Device Status:** Battery level, signal strength, session duration, last reading time, active alerts

**Advanced:** Gravity velocity, accelerometer (X/Y/Z), device stability, fermentation activity, firmware version

**📋 [Complete Sensor List →](SENSORS.md)**

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