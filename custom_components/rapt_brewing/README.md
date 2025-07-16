# RAPT Brewing Session Manager

A comprehensive Home Assistant integration for managing brewing sessions with RAPT Pill hydrometers.

## Features

### Core Functionality
- **Session Management**: Start, stop, pause, and resume brewing sessions
- **Real-time Monitoring**: Track gravity, temperature, and battery levels
- **Calculated Metrics**: Automatic ABV, attenuation, and fermentation rate calculations
- **Historical Tracking**: Store and analyze brewing session data over time
- **Smart Alerts**: Notifications for stuck fermentation, temperature issues, and more

### Sensors
- **Session Information**: Name, state, fermentation stage, duration
- **Gravity Readings**: Original, current, and target gravity
- **Calculated Values**: Alcohol percentage, attenuation, fermentation rate
- **Environmental**: Current and target temperature
- **Device Status**: Battery level, signal strength, last reading time
- **Statistics**: Total sessions, active alerts

### Controls
- **Buttons**: Start/stop/pause/resume session controls
- **Selects**: Fermentation stage selection, active session switching
- **Services**: Advanced session management and data export

### Alerts & Notifications
- **Stuck Fermentation**: Detects when fermentation has stopped
- **Temperature Alerts**: High/low temperature warnings
- **Fermentation Complete**: Notification when target gravity is reached
- **Low Battery**: Warning when RAPT Pill battery is low

## Prerequisites

1. **RAPT BLE Integration**: The core RAPT BLE integration must be installed and configured
2. **RAPT Pill Device**: A RAPT Pill hydrometer paired with Home Assistant
3. **Home Assistant**: Version 2023.9.0 or later

## Installation

### Method 1: HACS (Recommended)
1. Add this repository to HACS as a custom repository
2. Install "RAPT Brewing Session Manager" through HACS
3. Restart Home Assistant

### Method 2: Manual Installation
1. Copy the `rapt_brewing` folder to your `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Configuration** → **Integrations**
2. Click **Add Integration**
3. Search for "RAPT Brewing Session Manager"
4. Enter your RAPT device ID (found in the RAPT BLE integration)
5. Click **Submit**

## Usage

### Starting a Session
1. Use the "Start Brewing Session" button or service
2. Provide session name, recipe, and target values
3. The integration will begin tracking data automatically

### Monitoring Progress
- View real-time gravity and temperature readings
- Track calculated ABV and attenuation percentages
- Monitor fermentation rate trends
- Receive alerts for important events

### Managing Sessions
- Change fermentation stages as brewing progresses
- Add notes to sessions
- Export session data for analysis
- View historical session statistics

## Dashboard Configuration

Copy the contents of `dashboard_config.yaml` to create a comprehensive brewing dashboard with:
- Session control panel
- Real-time readings
- Historical charts
- Progress tracking
- Alert monitoring

## Services

### `rapt_brewing.start_brewing_session`
Start a new brewing session with specified parameters.

### `rapt_brewing.stop_brewing_session`
Stop the current brewing session.

### `rapt_brewing.add_session_note`
Add a note to the current session.

### `rapt_brewing.acknowledge_alert`
Acknowledge a brewing alert.

### `rapt_brewing.export_session_data`
Export session data in CSV or JSON format.

## Data Storage

Session data is stored locally in Home Assistant's storage system:
- All session data persists across restarts
- Historical data is preserved
- Configurable data retention periods

## Calculations

### Alcohol by Volume (ABV)
```
ABV = (OG - FG) × 131.25
```

### Apparent Attenuation
```
Attenuation = ((OG - FG) / (OG - TG)) × 100
```

### Fermentation Rate
```
Rate = ΔGravity / ΔTime (SG points per hour)
```

## Alerts

### Stuck Fermentation
Triggered when no significant gravity change occurs for 48 hours.

### Temperature Alerts
- High: > 30°C (86°F)
- Low: < 10°C (50°F)

### Fermentation Complete
Triggered when current gravity reaches target gravity ± 0.002 SG.

### Low Battery
Triggered when RAPT Pill battery drops below 20%.

## Troubleshooting

### Common Issues

**Integration not loading**
- Ensure RAPT BLE integration is installed and working
- Check device ID is correct
- Verify Home Assistant logs for errors

**No data updates**
- Check RAPT Pill is connected and transmitting
- Verify BLE connectivity
- Ensure device is within range

**Calculations incorrect**
- Verify original gravity is set correctly
- Check target gravity values
- Ensure sufficient data points for rate calculations

### Debug Logging
Enable debug logging by adding to `configuration.yaml`:
```yaml
logger:
  logs:
    custom_components.rapt_brewing: debug
```

## Support

For issues, feature requests, or contributions:
- GitHub: [your-github-repo]
- Home Assistant Community: [community-link]

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Acknowledgments

- RAPT (KegLand) for the excellent brewing hardware
- Home Assistant community for integration support
- Contributors and testers