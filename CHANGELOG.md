# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.1] - 2025-07-18

### 🔧 **Bug Fixes**
- Enhanced BLE parsing error logging to identify short packet issues
- Added detailed logging for legacy format packets to diagnose 9-byte packet truncation
- Repository cleanup: removed unnecessary setup files and redundant documentation

### 🧹 **Maintenance**
- Removed obsolete setup guides and reference files
- Cleaned up repository structure for better HACS compatibility

## [2.0.0] - 2025-01-16

### ⚡ **MAJOR UPDATE: Integrated Bluetooth Support**

This release completely eliminates the need for the separate RAPT BLE integration by incorporating direct Bluetooth Low Energy support.

### 🎯 **Breaking Changes**
- **No longer requires** separate RAPT BLE integration installation
- **Direct Bluetooth integration** - communicates directly with RAPT Pill devices
- **Updated configuration flow** with automatic device discovery
- **New dependency**: `bluetooth_adapters` instead of `rapt_ble`

### ✨ **New Features**
- **Automatic BLE Device Discovery**: Integration automatically finds RAPT Pill devices via Bluetooth
- **Integrated BLE Parser**: Built-in parsing of RAPT Pill Bluetooth advertisements
- **Real-time BLE Data**: Direct communication with RAPT Pill without cloud dependency
- **Enhanced Config Flow**: Visual device selection from discovered Bluetooth devices
- **Improved Device Management**: Better device identification and status monitoring

### 🔧 **Technical Improvements**
- **PassiveBluetoothProcessorCoordinator**: Efficient BLE scanning and data processing
- **Manufacturer ID Support**: Proper handling of RAPT (16722) and KegLand (17739) BLE identifiers
- **Binary Data Parsing**: Complete implementation of RAPT Pill data packet structure
- **Signal Strength Monitoring**: Real-time RSSI tracking for device connectivity
- **Battery Level Detection**: Direct battery status from BLE advertisements

### 📊 **Enhanced Data Sources**
- **Temperature**: Direct from BLE (-50°C to 100°C range validation)
- **Specific Gravity**: Direct from BLE (0.5 to 2.0 SG range validation)
- **Battery Level**: Direct from BLE (0-100% with validation)
- **Signal Strength**: Real-time RSSI from Bluetooth connection
- **Accelerometer Data**: X, Y, Z axis readings (for future features)

### 🔄 **Migration Guide**
**From v1.x to v2.0:**
1. **Remove** the separate RAPT BLE integration (if installed)
2. **Update** RAPT Brewing Session Manager via HACS
3. **Restart** Home Assistant
4. **Reconfigure** the integration - it will auto-discover your RAPT Pill
5. **Enjoy** seamless integrated Bluetooth support!

### 📋 **Prerequisites Updated**
- ~~RAPT BLE integration~~ (No longer needed!)
- Home Assistant 2023.9.0 or later
- Bluetooth integration enabled
- RAPT Pill hydrometer device

### 🐛 **Bug Fixes**
- **UI Configuration**: Fixed "cannot be added from UI" error
- **Device Validation**: Improved device detection and validation
- **Error Handling**: Better error messages and recovery
- **Memory Management**: Efficient BLE data processing

### 🚀 **Performance Improvements**
- **Direct BLE Access**: Eliminates middleman integration overhead
- **Optimized Parsing**: Native binary data parsing without external library overhead
- **Reduced Dependencies**: Fewer moving parts, more reliable operation
- **Local Processing**: All data processing happens locally, no cloud dependency

## [1.0.1] - 2025-01-16

### 🔧 **UI Configuration Fix**
- Added `config_flow: true` to manifest.json to enable UI setup
- Improved device validation to be more permissive
- Better error handling in configuration flow

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