# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-16

### Added
- Initial release of RAPT Brewing Session Manager
- Complete brewing session management (start, stop, pause, resume)
- Real-time monitoring of RAPT Pill data (gravity, temperature, battery)
- Automatic calculations for ABV, attenuation, and fermentation rate
- Smart brewing alerts (stuck fermentation, temperature warnings, completion)
- Historical data storage and session tracking
- Dashboard configuration for Lovelace UI
- Multi-stage fermentation support (primary, secondary, conditioning, packaging)
- Recipe integration and target tracking
- Data export functionality (CSV/JSON)
- Comprehensive sensor entities (16 total)
- Button controls for session management
- Select entities for stage and session switching
- Home Assistant services for advanced operations
- Persistent storage of brewing session data
- Alert acknowledgment system
- Session duration tracking
- Battery and signal strength monitoring
- Temperature trend analysis
- Fermentation rate calculations
- Progress indicators and completion detection

### Technical Features
- Integration with existing RAPT BLE component
- Proper Home Assistant entity structure
- Configuration flow for easy setup
- Localization support
- Error handling and validation
- Debug logging support
- HACS compatibility

### Dependencies
- Home Assistant 2023.9.0 or later
- RAPT BLE integration
- rapt-ble>=0.1.2 Python package

### Documentation
- Complete README with installation instructions
- Dashboard configuration examples
- Troubleshooting guide
- API service documentation
- Sensor entity reference