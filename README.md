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
Alerts automatically create Home Assistant persistent notifications in the UI. For external notifications, you have two options:

#### Option 1: Built-in Notification Service (Recommended)
First, ensure you have a notification service configured (mobile app, Telegram, email, etc.). Then:

1. Go to **Settings** → **Devices & Services** → **RAPT Brewing Session Manager**
2. Click **Configure**
3. Select your notification service from the dropdown (e.g., `notify.mobile_app_your_phone`)
4. Click **Submit**

The integration will automatically send alerts to your chosen notification service with rich data including alert type, session name, and brewing status.

**Popular notification services to set up first:**
- **Mobile App**: Install Home Assistant Companion app
- **Telegram**: Configure `telegram_bot` and `notify.telegram`
- **Email**: Set up `notify.smtp`
- **Discord**: Configure `notify.discord`
- **Ntfy.sh**: Configure `notify.rest` for ntfy.sh (see below)

#### Option 2: Custom Automations
For more control, create automations that trigger on alert changes.

**Example: Mobile App Notifications**
```yaml
automation:
  - alias: "RAPT Brewing Mobile Notifications"
    trigger:
      - platform: state
        entity_id: sensor.rapt_brewing_session_manager_active_alerts
        to: 
          - "1"
          - "2"
          - "3"
    condition:
      - condition: template
        value_template: "{{ states('sensor.rapt_brewing_session_manager_active_alerts') | int > 0 }}"
    action:
      - service: notify.mobile_app_your_phone_name
        data:
          title: "🍺 RAPT Brewing Alert"
          message: "{{ state_attr('sensor.rapt_brewing_session_manager_active_alerts', 'alerts')[0].message }}"
```

**Example: Telegram Notifications**
```yaml
# First configure Telegram in configuration.yaml
notify:
  - name: telegram_brewing
    platform: telegram
    chat_id: YOUR_CHAT_ID

# Then create automation
automation:
  - alias: "RAPT Brewing Telegram Notifications"
    trigger:
      - platform: state
        entity_id: sensor.rapt_brewing_session_manager_active_alerts
        to: 
          - "1"
          - "2"
          - "3"
    action:
      - service: notify.telegram_brewing
        data:
          title: "🍺 Brewing Alert"
          message: "{{ state_attr('sensor.rapt_brewing_session_manager_active_alerts', 'alerts')[0].message }}"
```

### Ntfy.sh Configuration

[Ntfy.sh](https://ntfy.sh) is a simple pub-sub notification service. Here's how to set it up:

#### Step 1: Configure ntfy.sh in Home Assistant

Add to your `configuration.yaml`:

```yaml
notify:
  - name: ntfy_brewing
    platform: rest
    resource: https://ntfy.sh/your-unique-topic-name
    method: POST_JSON
    headers:
      Title: "🍺 RAPT Brewing Alert"
      Priority: "default"
      Tags: "beer,brewing"
    message_param_name: message
    title_param_name: title
```

Replace `your-unique-topic-name` with a unique topic name (e.g., `rapt-brewing-alerts-yourname123`).

#### Step 2: Configure in RAPT Integration

1. Restart Home Assistant
2. Go to **Settings** → **Devices & Services** → **RAPT Brewing Session Manager**
3. Click **Configure**
4. Select `notify.ntfy_brewing` from the dropdown
5. Click **Submit**

#### Step 3: Subscribe to notifications

**On your phone:**
1. Install the ntfy app ([Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) | [iOS](https://apps.apple.com/us/app/ntfy/id1625396347))
2. Subscribe to your topic: `your-unique-topic-name`
3. You'll receive push notifications for all brewing alerts

**On your computer:**
- Visit `https://ntfy.sh/your-unique-topic-name` in your browser
- Or use the ntfy CLI: `ntfy subscribe your-unique-topic-name`

#### Advanced ntfy.sh Configuration

For more features like icons, actions, and priorities:

```yaml
notify:
  - name: ntfy_brewing_advanced
    platform: rest
    resource: https://ntfy.sh/your-unique-topic-name
    method: POST_JSON
    headers:
      Priority: "high"  # low, default, high, max
      Tags: "beer,🍺,brewing"
      Icon: "https://raw.githubusercontent.com/sbaird123/rapt-brewing-hacs/main/icon.png"
    message_param_name: message
    title_param_name: title
    data:
      click: "https://your-home-assistant.com/lovelace/brewing"  # Open brewing dashboard
      actions: |
        [
          {
            "action": "view", 
            "label": "View Dashboard", 
            "url": "https://your-home-assistant.com/lovelace/brewing"
          }
        ]
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