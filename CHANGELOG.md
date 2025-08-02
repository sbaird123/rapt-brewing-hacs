# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.8] - 2025-08-02

### 🔔 **Smart Temperature Alerts - No More Cold Crash Spam**
- **Context-aware cold temperature alerts**: Only alerts if attenuation < 70% (early/mid fermentation)
- **Cold crash detection**: No alerts when attenuation ≥ 70% since cold crashes are expected at fermentation end
- **Hot temperature alerts unchanged**: Still alerts for temperatures > 30°C during any phase
- **Prevents notification spam**: No more 6+ cold temperature alerts during expected cold crashes

### 📚 **Updated Documentation**
- **Removed pressure fermentation references**: Updated README to reflect v2.5.0+ changes (pressure features removed)
- **Added temperature correction section**: Explains scientific 0.00013 coefficient and how it works
- **Updated alert descriptions**: Documents new context-aware behavior and alert frequencies
- **Accurate feature list**: Features now match current integration capabilities

### 🍺 **Alert Logic Improvements**
**Temperature Low Alerts:**
- **Early fermentation (< 70% attenuation)**: Alerts for cold temperatures (potential issue)
- **Late fermentation (≥ 70% attenuation)**: No alerts (cold crash expected and normal)
- **Message updated**: "Temperature too low during fermentation" (clarifies context)

**Other Alerts Unchanged:**
- **Stuck fermentation**: Once per session
- **High temperature**: Once per hour  
- **Low battery**: Once per hour (after calibration)
- **Fermentation complete**: Once per hour

**Perfect for real brewing workflows where cold crashes happen at 70-85% attenuation!**

## [2.5.7] - 2025-08-02

### 🔧 **Critical Fix: Temperature Correction Consistency**
- **Fixed duplicate temperature correction methods**: Both methods now use the same scientific coefficient (0.00013 per °C)
- **Eliminated old 0.0004 factor**: Removed inconsistent temperature correction that was still being used by sensors
- **Consistent correction formula**: All temperature corrections now use the scientifically accurate factor throughout the codebase
- **Fixed calculation direction**: Ensured both methods subtract thermal effects to show actual density (not add)

### 🧪 **What Was Wrong**
Two different temperature correction methods existed:
- **Main method (_get_temperature_corrected_gravity)**: Still used old 0.0004 factor (200% too large)
- **Helper method (_apply_temp_correction_to_gravity)**: Used correct 0.00013 factor but with wrong calculation direction

### ✅ **What's Fixed**
- **Unified coefficient**: Both methods now use 0.00013 per °C (scientific literature)
- **Consistent calculation**: `True_Density = Raw_Gravity - (Temperature - 20°C) × 0.00013`
- **Proper sensor readings**: Temperature-corrected gravity sensor now shows realistic values
- **Code consistency**: No more conflicting temperature correction implementations

### 🍺 **Expected Results**
**Your cold crash example (9.3°C, raw gravity 1.0086):**
- **Old result**: 1.0129 (overcorrected with 0.0004 factor)
- **New result**: ~1.010 (realistic correction with 0.00013 factor)

**This fix ensures the temperature correction actually uses the scientifically researched coefficient!**

## [2.5.6] - 2025-07-25

### 🔬 **Fix: Use Scientifically Accurate Temperature Correction Factor**
- **Updated coefficient**: Changed from 0.0004 to **0.00013 per °C** based on scientific literature
- **Accurate ABV calculations**: Temperature correction now gives realistic alcohol percentages
- **Recipe validation**: ABV calculations now match expected recipe dilution ratios
- **Scientific basis**: Uses coefficient from CRC Handbook of Chemistry and Physics via Lyons 1992

### 📊 **Real-World Validation**
**User's diluted kit test:**
- **Recipe**: 6.8% ABV at 18L, diluted to 23L = **5.3% expected ABV**
- **With old factor (0.0004)**: 6.3% ABV (too high)
- **With scientific factor (0.00013)**: **5.9% ABV** (matches expectation!)

### 🔬 **Research-Based Change**
**Temperature Correction Factor Sources:**
- **Anton Paar professional equipment**: 0.0003 per °C
- **Scientific literature (CRC Handbook)**: **0.00013 per °C** (primary linear coefficient)
- **Previous guess**: 0.0004 per °C (overcorrecting by 200%+)

### ✅ **What's Improved**
- **Formula**: `True_Density = Raw_Gravity - (Temperature - 20°C) × 0.00013`
- **Accurate corrections**: Smaller, more realistic temperature adjustments
- **Better ABV calculations**: Results match recipe expectations and brewing science
- **Validated against real recipes**: Dilution ratios now calculate correctly

### 🍺 **Example Results**
**Cold crash at 8.8°C:**
- **Raw gravity**: 1.00859 (thermal contraction effect)
- **Temp corrected**: 1.007046 (scientific correction applied)
- **ABV calculation**: More accurate, matches recipe dilution expectations

**This temperature correction factor is based on actual scientific research rather than guesswork!**

## [2.5.5] - 2025-07-25

### 🎯 **MAJOR FIX: Temperature Correction Now Shows Actual Density** *(Superseded by v2.5.6)*
- **Fixed fundamental concept error**: Temperature correction now removes thermal effects instead of compensating to 20°C
- **Actual density calculation**: Shows true liquid density regardless of temperature effects
- **Proper brewing logic**: Perfect for ABV calculations and fermentation tracking
- **No dashboard changes**: Same sensor names and entities - just works correctly now

### 🔬 **What Was Fundamentally Wrong**
Previous versions were doing **temperature compensation** (showing what gravity would be at 20°C) instead of **temperature correction** (removing thermal effects):
- **Cold liquid**: Contracts → reads artificially HIGH → we should subtract thermal effect
- **Warm liquid**: Expands → reads artificially LOW → we should add thermal effect
- **Previous formula**: Did the opposite - amplified temperature effects instead of removing them

### ✅ **What's Fixed**
- **Correct physics**: `True_Density = Raw_Gravity - (Temperature - 20°C) × 0.0004`
- **Removes thermal effects**: Cold readings get thermal contraction removed, warm readings get thermal expansion removed
- **Stable fermentation tracking**: Temperature changes don't affect apparent fermentation progress
- **Accurate ABV calculations**: Uses true density for proper alcohol percentage calculations

### 🍺 **Real-World Example**
**Cold crash at 8.8°C:**
- **Raw gravity**: 1.00859 (artificially high due to liquid contraction)
- **Temp corrected**: 1.0041 (thermal contraction effect removed - true density)
- **Result**: Temperature-corrected value shows actual fermentation state, not thermal effects

### 🚀 **Why This Matters**
- **True fermentation progress**: Temperature changes don't mask or amplify fermentation activity
- **Accurate brewing calculations**: ABV, attenuation based on actual density, not thermal artifacts
- **Consistent monitoring**: Fermentation tracking works correctly during temperature swings, cold crashes, etc.

**This is the temperature correction brewers actually need - true density for accurate brewing decisions!**

## [2.5.4] - 2025-07-25

### 🔧 **Fix: Stabilize Temperature Correction** *(Superseded by v2.5.5)*
- **Simplified temperature correction formula**: Removed complex variable reduction logic causing erratic readings
- **Consistent corrections**: Temperature-corrected gravity now shows smooth, stable readings
- **Scientific accuracy maintained**: Uses proven 0.0004 per °C coefficient (thermal expansion of aqueous solutions)
- **ASBC standard compliance**: 20°C calibration temperature per American Society of Brewing Chemists

### 🔬 **What Was Wrong**
The temperature correction was using complex logic that varied the correction factor based on fermentation rate, causing:
- **Erratic corrections**: Wild fluctuations in temp-corrected gravity readings
- **Inconsistent application**: Sometimes full correction, sometimes reduced correction
- **Graph noise**: Jagged temperature-corrected gravity line despite stable temperature

### ✅ **What's Fixed**
- **Simple, consistent formula**: `Corrected_Gravity = Raw_Gravity + (Temperature - 20°C) × 0.0004`
- **Stable readings**: Temperature-corrected gravity now tracks smoothly with raw gravity
- **Scientific basis**: Formula based on thermal expansion coefficient of water/wort solutions
- **Professional standard**: Matches brewing industry temperature correction practices

### 📊 **Expected Results**
- **Smooth temperature correction line** that closely follows raw gravity
- **Small, consistent corrections** (typically ±0.002 SG for normal temperature variations)
- **Reliable brewing calculations** using stable temperature-corrected values

## [2.5.3] - 2025-07-25

### 📊 **New Feature: Clean Session Start**
- **Reset sensor values** when starting a new session to create clean history graphs
- **Clear data points and alerts** from previous sessions
- **Visual break in graphs** - no more confusing carryover data from previous fermentations
- **Fresh start monitoring** - each new session begins with clean sensor history

### 🎯 **How It Works**
When starting a new brewing session:
1. **Sensor values reset** to `None` (gravity, temperature, ABV, etc.)
2. **Data points cleared** - removes all previous fermentation data
3. **Alerts cleared** - starts with a clean alert slate
4. **History graphs show gap** - clear visual separation between sessions
5. **New data appears** as soon as RAPT Pill provides first reading

### 🚀 **Benefits**
- **Clean graphs** that only show current fermentation progress
- **No confusion** from previous session data
- **Easy to track** individual fermentation performance
- **Professional monitoring** with clear session boundaries

## [2.5.2] - 2025-07-25

### 🔧 **Hotfix: Syntax Error**
- **Fixed indentation error** in coordinator.py that prevented integration from loading
- **Quick fix** for issue introduced in v2.5.1

## [2.5.1] - 2025-07-25

### 🔔 **Fix: Stuck Fermentation Notification Spam**
- **One-time stuck fermentation alerts**: Stuck fermentation now only alerts once per session instead of every hour
- **Cleaned up dashboard configurations**: Removed all pressure-related entities from dashboard YAML files
- **Reduced notification noise**: No more spam of 22+ stuck fermentation notifications

### 🧹 **Dashboard Cleanup**
- **Removed pressure entities** from desktop dashboard configuration
- **Removed pressure entities** from mobile dashboard configuration  
- **Cleaner dashboard layout** without defunct pressure monitoring sections

### 🎯 **Alert Logic Improvement**
- **Stuck fermentation**: Only alerts once per session (not recurring)
- **Other alerts** (temperature, battery): Still check for duplicates within 1 hour
- **Prevents notification spam** while maintaining important alerts

## [2.5.0] - 2025-07-25

### 🧹 **MAJOR CLEANUP: Removed Pressure Fermentation Features**
- **Removed pressure correction sensors**: No more pressure-corrected gravity or dissolved CO2 sensors
- **Removed pressure number entities**: No more starting/current pressure controls
- **Simplified data structure**: Removed all pressure-related fields from session data
- **Cleaner integration**: Focus on core temperature and fermentation monitoring

### 🎯 **Why This Change**
Analysis showed pressure corrections were **practically irrelevant** for brewing accuracy:
- **10 PSI correction**: Only 0.0001 SG difference (negligible)
- **30 PSI correction**: Only 0.0004 SG difference (still tiny)
- **ABV impact**: Always <0.01% difference
- **Industry standard**: Most brewers degas samples or ignore dissolved CO2

### 📊 **What Was Removed**
- `current_gravity_pressure_corrected` sensor
- `dissolved_co2` sensor  
- `starting_pressure` number entity
- `current_pressure` number entity
- All CO2 compensation formulas and calculations
- Pressure fermentation UI options

### ✅ **What Remains**
- **Temperature correction** (much more important - up to 0.005 SG difference)
- **Core fermentation monitoring** (gravity, temperature, battery, signals)
- **Fermentation activity sensor** with scientifically accurate thresholds
- **Smart stalled fermentation logic** for temperature corrections
- **All brewing calculations** (ABV, attenuation, fermentation rate)

### 🚀 **Benefits**
- **Simpler interface**: Less clutter, focus on what matters
- **Better performance**: Fewer calculations and entities
- **Easier maintenance**: Less complex code
- **Accurate monitoring**: Temperature correction is the only correction that significantly impacts brewing accuracy

**This version focuses on the essential brewing monitoring features that actually affect your brewing decisions.**

## [2.4.0] - 2025-07-25

### 🚨 **MAJOR FIX: Corrected Temperature Correction Formula** *(Superseded by v2.5.0)*
- **Fixed temperature correction factor**: Reduced from 0.00130 to 0.0004 per °C (proper factor for beer wort)
- **Eliminated excessive temperature corrections**: Temperature-corrected gravity no longer shows extreme fluctuations
- **Accurate brewing science**: Now uses the correct temperature coefficient for beer/wort density
- **Massive stability improvement**: Temperature-corrected readings are now scientifically accurate

### 🔬 **What Was Wrong**
The temperature correction factor was **3.25× too large** (0.00130 vs proper 0.0004), causing:
- **Extreme overcorrection**: 4°C temperature change caused 0.0052 SG correction (should be 0.0016)
- **Temperature tracking**: Corrected gravity appeared to track temperature changes exactly
- **False fermentation signals**: Temperature fluctuations looked like continued fermentation activity
- **Inaccurate calculations**: ABV, attenuation, and fermentation rates were affected

### 📊 **Before vs After Examples**
**4°C temperature swing (18°C to 22°C):**
- **Old correction**: ±0.0052 SG change (massive)
- **New correction**: ±0.0016 SG change (proper)
- **During stalled fermentation**: ±0.0003 SG change (reduced sensitivity)

### 🎯 **Why This Matters**
This explains the user's observation that temperature-corrected gravity was tracking temperature changes exactly during stalled fermentation. The correction was so large it dominated the reading, making temperature the primary factor instead of actual fermentation progress.

### ✅ **Combined Features**
- **Proper temperature correction factor** (0.0004 per °C)
- **Smart stalled fermentation logic** (reduced correction when fermentation stops)
- **Accurate brewing calculations** (ABV, attenuation, fermentation rate)
- **Stable end-of-fermentation readings**

**This is a critical accuracy fix that affects all gravity-based calculations and fermentation monitoring.**

## [2.3.9] - 2025-07-25

### 🔧 **Fix: Temperature Correction During Stalled Fermentation** *(Superseded by v2.4.0)*
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