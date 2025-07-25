# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.9] - 2025-07-25

### 🔧 **Fix: Temperature Correction During Stalled Fermentation**
- **Fixed temperature-corrected gravity bouncing**: Temperature corrected gravity no longer tracks temperature changes when fermentation is stalled
- **Smart correction reduction**: Reduces temperature correction sensitivity by 80% when fermentation rate is very low (stalled)
- **Improved end-of-fermentation accuracy**: Temperature corrected gravity now stays stable when fermentation is complete
- **Prevents false activity**: Eliminates the appearance of continued fermentation activity from temperature fluctuations alone

### 🍺 **Why This Matters**
When fermentation stalls, the raw gravity reading still changes with temperature, but the actual fermentable content is stable. The old temperature correction made it appear that fermentation was still active when it was just temperature-driven density changes.

### 📊 **Technical Details**
- **Very stalled fermentation** (≤2× stuck threshold): 20% of normal temperature correction
- **Slow fermentation** (≤slow threshold): 60% of normal temperature correction  
- **Active fermentation**: Full temperature correction as before
- **Unified correction logic**: Both sensor and coordinator use the same improved algorithm

## [2.3.8] - 2025-07-18

### 🔧 **Fix: Import Error in Fermentation Activity Sensor**
- **Fixed bad import statement**: Changed `from ..const import` to `from .const import`
- **Resolved sensor unavailable**: Fermentation activity sensor crashed due to incorrect relative import
- **Restored scientific thresholds**: Sensor now properly uses the new accurate fermentation rate constants

### 🐛 **What Broke in v2.3.7**
The fermentation activity sensor showed "unavailable" due to a Python import error when trying to access the new scientific threshold constants.

## [2.3.7] - 2025-07-18

### 🔬 **Major Fix: Scientifically Accurate Fermentation Thresholds**
- **Fixed incorrect fermentation rate thresholds**: Updated based on real brewing science and data
- **Corrected stuck fermentation detection**: Changed from 24 points/day to 1 point/day threshold
- **Accurate activity classification**: Thresholds now match actual fermentation rates from brewing studies
- **Aligned detection systems**: Both stuck fermentation alerts and activity sensor use same scientific thresholds

### 📊 **Real Brewing Science Applied**
Based on actual fermentation data from Double IPAs and brewing research:
- **Vigorous**: >19 points/day (peak fermentation)
- **Active**: >10 points/day (healthy fermentation)
- **Moderate**: >2 points/day (steady progress)
- **Slow**: >1 point/day (slow but progressing)  
- **Inactive/Stuck**: ≤1 point/day (effectively stalled)

### 🚨 **Critical Accuracy Fix**
Previous thresholds were **10-100x too high**, causing:
- Stuck fermentation detection at 24+ points/day (should be ≤1)
- Activity sensor showing "Moderate" for truly stalled fermentation
- Misalignment between alerts and sensor readings

Now both systems use the same scientifically accurate thresholds based on real brewing data.

## [2.3.6] - 2025-07-18

### 🔧 **Fix: Fermentation Activity Sensor Unavailable**
- **Fixed timezone mismatch**: Changed `datetime.now()` to `dt_util.now()` in fermentation activity calculation
- **Resolved "unavailable" sensor**: Fermentation activity sensor now properly displays activity levels
- **Consistent datetime handling**: All timestamps now use timezone-aware datetime objects

### 🐛 **What Was Wrong**
The fermentation activity sensor was showing "unavailable" due to a timezone mismatch introduced in v2.3.3. The sensor used naive datetime while data points used timezone-aware datetime, preventing proper timestamp comparisons.

## [2.3.5] - 2025-07-18

### 🔋 **Fix: Battery Calibration Threshold**
- **Corrected calibration threshold**: Changed from >5% to >0% for battery calibration
- **Proper low battery detection**: 1% battery is calibrated and should trigger low battery warning
- **More accurate logic**: Only 0% indicates uncalibrated state, any other percentage is a real reading

### 🎯 **Why This Matters**
A battery reading 1% is definitely calibrated and genuinely low - it should trigger a warning immediately. Only 0% readings indicate an uncalibrated/stuck state.

## [2.3.4] - 2025-07-18

### 🔋 **Alert Fix: Smart Battery Calibration**
- **Eliminated false low battery warnings**: No more alerts when battery starts at 0% (uncalibrated)
- **Automatic calibration detection**: Marks battery as calibrated when first reading above 0% is detected
- **Smart warning logic**: Low battery alerts (at 20%) only trigger after battery calibration
- **Persistent calibration state**: Once calibrated, continues monitoring throughout the session

### 🚫 **What's Fixed**
- **No more 0% startup alerts**: Uncalibrated RAPT Pill batteries won't trigger false warnings
- **Proper calibration timing**: Detects when battery provides real readings (>0%)
- **Accurate low battery detection**: 20% threshold only applies to calibrated batteries

### 🔋 **How It Works**
1. **Session starts**: Battery 0% → No warnings (uncalibrated)
2. **Battery calibrates**: First reading >0% → Marked as calibrated + logged
3. **Normal monitoring**: Warnings trigger if battery drops below 20%

## [2.3.3] - 2025-07-18

### 🔧 **Sensor Fix: Fermentation Activity Smoothing**
- **Fixed jumpy fermentation activity sensor**: Now uses rolling average over the last hour instead of just latest readings
- **More stable activity readings**: Eliminates rapid bouncing between "active, slow, active, inactive" states
- **Better end-of-fermentation detection**: Provides consistent readings for nearly finished brews
- **Improved algorithm**: Averages gravity velocity and fermentation rate data over 60 minutes for accurate trends

### 🍺 **Why This Matters**
The fermentation activity sensor was too reactive to momentary fluctuations, making it unusable for tracking fermentation progress. Now it provides stable, meaningful readings that reflect actual fermentation trends rather than noise.

## [2.3.2] - 2025-07-18

### 🔧 **Dashboard Fix: Mobile Chart**
- **Added pressure-corrected gravity to mobile dashboard chart**: Mobile users can now see all three gravity readings (raw, temp corrected, pressure corrected)
- **Complete pressure monitoring on mobile**: Mobile dashboard now shows the same gravity comparison as desktop

## [2.3.1] - 2025-07-18

### 🔧 **Bug Fix: Pressure Fermentation Logic**
- **Fixed pressure fermentation activation**: Now enables when any pressure setting is configured (not just starting pressure > 0)
- **Improved real-world workflow**: Supports typical brewing where fermentation starts at 0 PSI and builds pressure during fermentation
- **Pressure correction now works properly**: Activates when current pressure > 0, regardless of starting pressure

### 🍺 **Why This Matters**
Most fermentations start at atmospheric pressure (0 PSI) and build pressure from CO2 production or spunding valves. The previous logic incorrectly required starting pressure > 0 to enable pressure fermentation mode.

## [2.3.0] - 2025-07-18

### 🚀 **MAJOR FEATURE: Pressure Fermentation Support**

This release adds comprehensive pressure fermentation monitoring with advanced CO2 compensation calculations.

### ✨ **New Features**
- **Pressure Fermentation Mode**: Enable pressure brewing with CO2 solubility compensation
- **CO2 Compensation**: Accurate gravity readings that account for dissolved CO2 
- **Temperature-Dependent Calculations**: CO2 solubility adjusts based on fermentation temperature
- **Pressure Monitoring**: Track starting and current vessel pressure in PSI
- **True Gravity Readings**: Removes CO2 bias for accurate fermentation tracking
- **Dissolved CO2 Tracking**: Monitor CO2 levels throughout fermentation

### 📊 **New Sensors & Controls**
- `starting_pressure` - Number entity for initial fermentation pressure
- `current_pressure` - Number entity for current vessel pressure  
- `current_gravity_pressure_corrected` - CO2-compensated gravity sensor
- `dissolved_co2` - Dissolved CO2 levels sensor (g/L)

### 🎛️ **Enhanced Session Management**
- Pressure fermentation toggle in session creation
- Automatic pressure mode activation when pressure > 0
- Enhanced dashboard with pressure monitoring sections
- Mobile-friendly pressure tracking interface

### 🧮 **Brewing Science Implementation**
- **CO2 Solubility**: ~1.7 g/L per PSI at 20°C (Henry's Law)
- **Temperature Correction**: 2% decrease per °C above 20°C
- **Gravity Compensation**: ~0.0004 SG per gram dissolved CO2
- **Pressure-Corrected ABV**: Uses true gravity for accurate alcohol calculations

### 📚 **Documentation**
- Complete pressure fermentation guide in README
- Technical calculation explanations
- Updated sensor documentation
- Enhanced dashboard configurations for pressure monitoring

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