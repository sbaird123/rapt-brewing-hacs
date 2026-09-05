"""Constants for RAPT Brewing integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "rapt_brewing"

# Default values
DEFAULT_SCAN_INTERVAL: Final = 60
DEFAULT_SESSION_TIMEOUT: Final = 24 * 60 * 60  # 24 hours

# Entity IDs
ENTITY_ID_SESSION_STATUS: Final = "session_status"
ENTITY_ID_SESSION_NAME: Final = "session_name"
ENTITY_ID_SESSION_RECIPE: Final = "session_recipe"
ENTITY_ID_ORIGINAL_GRAVITY: Final = "original_gravity"
ENTITY_ID_FINAL_GRAVITY: Final = "final_gravity"
ENTITY_ID_CURRENT_GRAVITY: Final = "current_gravity"
ENTITY_ID_ALCOHOL_PERCENTAGE: Final = "alcohol_percentage"
ENTITY_ID_ATTENUATION: Final = "attenuation"
ENTITY_ID_FERMENTATION_RATE: Final = "fermentation_rate"
ENTITY_ID_TEMPERATURE: Final = "temperature"
ENTITY_ID_BATTERY_LEVEL: Final = "battery_level"
ENTITY_ID_SIGNAL_STRENGTH: Final = "signal_strength"

# Brewing session states
SESSION_STATE_IDLE: Final = "idle"
SESSION_STATE_ACTIVE: Final = "active"
SESSION_STATE_PAUSED: Final = "paused"
SESSION_STATE_COMPLETED: Final = "completed"

# Fermentation stages
FERMENTATION_STAGE_PRIMARY: Final = "primary"
FERMENTATION_STAGE_SECONDARY: Final = "secondary"
FERMENTATION_STAGE_CONDITIONING: Final = "conditioning"
FERMENTATION_STAGE_PACKAGING: Final = "packaging"

# Alert types
ALERT_TYPE_STUCK_FERMENTATION: Final = "stuck_fermentation"
ALERT_TYPE_TEMPERATURE_HIGH: Final = "temperature_high"
ALERT_TYPE_TEMPERATURE_LOW: Final = "temperature_low"
ALERT_TYPE_FERMENTATION_COMPLETE: Final = "fermentation_complete"
ALERT_TYPE_LOW_BATTERY: Final = "low_battery"
ALERT_TYPE_HEATER_INEFFECTIVE: Final = "heater_ineffective"

# Data keys
DATA_SESSIONS: Final = "sessions"
DATA_CURRENT_SESSION: Final = "current_session"
DATA_ALERTS: Final = "alerts"
DATA_SETTINGS: Final = "settings"

# Configuration keys
CONF_RAPT_DEVICE_ID: Final = "rapt_device_id"
CONF_TARGET_GRAVITY: Final = "target_gravity"
CONF_TARGET_TEMPERATURE: Final = "target_temperature"
CONF_NOTIFICATION_SERVICE: Final = "notification_service"
CONF_SOURCE_TYPE: Final = "source_type"
CONF_GRAVITY_ENTITY: Final = "gravity_entity"
CONF_TEMPERATURE_ENTITY: Final = "temperature_entity"
CONF_BATTERY_ENTITY: Final = "battery_entity"
CONF_SIGNAL_ENTITY: Final = "signal_entity"
CONF_API_EMAIL: Final = "api_email"
CONF_API_SECRET: Final = "api_secret"
CONF_HYDROMETER_ID: Final = "hydrometer_id"

# Option keys (configurable alert thresholds, calibration and display)
CONF_STUCK_FERMENTATION_HOURS: Final = "stuck_fermentation_hours"
CONF_TEMPERATURE_HIGH_THRESHOLD: Final = "temperature_high_threshold"
CONF_TEMPERATURE_LOW_THRESHOLD: Final = "temperature_low_threshold"
CONF_LOW_BATTERY_THRESHOLD: Final = "low_battery_threshold"
CONF_OFFLINE_TIMEOUT_MINUTES: Final = "offline_timeout_minutes"
CONF_GRAVITY_OFFSET: Final = "gravity_offset"
CONF_TEMPERATURE_OFFSET: Final = "temperature_offset"
CONF_GRAVITY_UNIT: Final = "gravity_unit"

# Option keys (temperature control)
CONF_HEATER_SWITCH: Final = "heater_switch"
CONF_COOLER_SWITCH: Final = "cooler_switch"
CONF_HEAT_PROPORTIONAL_BAND: Final = "heat_proportional_band"
CONF_HEAT_CYCLE_MINUTES: Final = "heat_cycle_minutes"
CONF_HEAT_INTEGRAL_HOURS: Final = "heat_integral_hours"
CONF_COOL_DEADBAND: Final = "cool_deadband"
CONF_COOL_MIN_ON_MINUTES: Final = "cool_min_on_minutes"
CONF_COOL_MIN_OFF_MINUTES: Final = "cool_min_off_minutes"
CONF_CHANGEOVER_MINUTES: Final = "changeover_minutes"
CONF_MAX_HEAT_OVERSHOOT: Final = "max_heat_overshoot"
CONF_ABSOLUTE_MAX_TEMPERATURE: Final = "absolute_max_temperature"

# Data source types
SOURCE_TYPE_BLUETOOTH: Final = "bluetooth"
SOURCE_TYPE_ENTITY: Final = "entity"
SOURCE_TYPE_CLOUD: Final = "cloud"

# Gravity display units
GRAVITY_UNIT_SG: Final = "sg"
GRAVITY_UNIT_PLATO: Final = "plato"

# Cloud polling
CLOUD_SCAN_INTERVAL: Final = 300  # seconds

# Events
EVENT_RAPT_BREWING_ALERT: Final = "rapt_brewing_alert"

# Default alert thresholds
DEFAULT_STUCK_FERMENTATION_HOURS: Final = 48
DEFAULT_TEMPERATURE_HIGH_THRESHOLD: Final = 30.0  # Celsius
DEFAULT_TEMPERATURE_LOW_THRESHOLD: Final = 10.0  # Celsius
DEFAULT_LOW_BATTERY_THRESHOLD: Final = 20  # Percentage
DEFAULT_OFFLINE_TIMEOUT_MINUTES: Final = 15  # Direct Bluetooth / entity sources
DEFAULT_OFFLINE_TIMEOUT_MINUTES_CLOUD: Final = 120  # Pills report to the cloud much less often

# Default temperature control tuning
# A fermenter heat belt is low wattage and heats the vessel wall, so the wort
# temperature lags 30-60 minutes behind switching. Time-proportional control
# over a 15 minute window keeps switching gentle while tracking the setpoint.
DEFAULT_HEAT_PROPORTIONAL_BAND: Final = 1.0  # °C below target for 100% duty
DEFAULT_HEAT_CYCLE_MINUTES: Final = 15
DEFAULT_HEAT_INTEGRAL_HOURS: Final = 2.0  # trims out proportional droop; 0 disables
DEFAULT_COOL_DEADBAND: Final = 0.5  # °C above target before the fridge starts
DEFAULT_COOL_MIN_ON_MINUTES: Final = 3
DEFAULT_COOL_MIN_OFF_MINUTES: Final = 5  # compressor short-cycle protection
DEFAULT_CHANGEOVER_MINUTES: Final = 10  # deadtime between heating and cooling
DEFAULT_MAX_HEAT_OVERSHOOT: Final = 2.0  # never heat above target + this
DEFAULT_ABSOLUTE_MAX_TEMPERATURE: Final = 30.0  # hard cutout regardless of target
CONTROL_TICK_SECONDS: Final = 30  # how often the control law is evaluated

# Fermentation rate thresholds based on real brewing data (SG/hour)
FERMENTATION_RATE_VIGOROUS: Final = 0.0008  # >19 points/day - peak fermentation
FERMENTATION_RATE_ACTIVE: Final = 0.0004    # >10 points/day - good fermentation
FERMENTATION_RATE_MODERATE: Final = 0.0001  # >2 points/day - steady progress
FERMENTATION_RATE_SLOW: Final = 0.00004     # >1 point/day - slow but progressing
FERMENTATION_RATE_STUCK: Final = 0.00004    # ≤1 point/day - effectively stalled

# Plausible physical bounds — readings outside these are rejected as bad data
# so a single spike can't poison current_gravity / OG / data_points.
GRAVITY_MIN: Final = 0.950
GRAVITY_MAX: Final = 1.200
TEMPERATURE_MIN: Final = -10.0
TEMPERATURE_MAX: Final = 60.0
BATTERY_MIN: Final = 0
BATTERY_MAX: Final = 100