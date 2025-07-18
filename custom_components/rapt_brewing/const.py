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

# Data keys
DATA_SESSIONS: Final = "sessions"
DATA_CURRENT_SESSION: Final = "current_session"
DATA_ALERTS: Final = "alerts"
DATA_SETTINGS: Final = "settings"

# Configuration keys
CONF_RAPT_DEVICE_ID: Final = "rapt_device_id"
CONF_TARGET_GRAVITY: Final = "target_gravity"
CONF_TARGET_TEMPERATURE: Final = "target_temperature"
CONF_FERMENTATION_ALERTS: Final = "fermentation_alerts"
CONF_TEMPERATURE_ALERTS: Final = "temperature_alerts"
CONF_ALERT_THRESHOLDS: Final = "alert_thresholds"
CONF_NOTIFICATION_SERVICE: Final = "notification_service"

# Default alert thresholds
DEFAULT_STUCK_FERMENTATION_HOURS: Final = 48
DEFAULT_TEMPERATURE_HIGH_THRESHOLD: Final = 30.0  # Celsius
DEFAULT_TEMPERATURE_LOW_THRESHOLD: Final = 10.0  # Celsius
DEFAULT_LOW_BATTERY_THRESHOLD: Final = 20  # Percentage