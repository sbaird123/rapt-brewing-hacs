"""Coordinator for RAPT Brewing integration."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
import homeassistant.util.dt as dt_util
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

if TYPE_CHECKING:
    from homeassistant.components.bluetooth.passive_update_processor import (
        PassiveBluetoothProcessorCoordinator,
    )
    from .ble_device import RAPTPillBluetoothDeviceData, RAPTPillSensorData
from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    CONF_RAPT_DEVICE_ID,
    CONF_NOTIFICATION_SERVICE,
    SESSION_STATE_ACTIVE,
    SESSION_STATE_IDLE,
    ALERT_TYPE_STUCK_FERMENTATION,
    ALERT_TYPE_TEMPERATURE_HIGH,
    ALERT_TYPE_TEMPERATURE_LOW,
    ALERT_TYPE_FERMENTATION_COMPLETE,
    ALERT_TYPE_LOW_BATTERY,
    DEFAULT_STUCK_FERMENTATION_HOURS,
    DEFAULT_TEMPERATURE_HIGH_THRESHOLD,
    DEFAULT_TEMPERATURE_LOW_THRESHOLD,
    DEFAULT_LOW_BATTERY_THRESHOLD,
    FERMENTATION_RATE_STUCK,
    FERMENTATION_RATE_SLOW,
)
from .data import RAPTBrewingData, BrewingSession, DataPoint, Alert

if TYPE_CHECKING:
    from homeassistant.helpers.entity_registry import EntityRegistry

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = "rapt_brewing_sessions"


class RAPTBrewingCoordinator(DataUpdateCoordinator[RAPTBrewingData]):
    """Coordinator for RAPT Brewing integration."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.entry = entry
        self.store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.data = RAPTBrewingData()
        self._rapt_device_id = entry.data.get(CONF_RAPT_DEVICE_ID)
        self._ble_cancel_callback = None
        
        # Initialize BLE processor - import at runtime to avoid blocking
        from homeassistant.components.bluetooth.passive_update_processor import (
            PassiveBluetoothProcessorCoordinator,
        )
        from .ble_device import RAPTPillBluetoothDeviceData, RAPTPillSensorData
        
        _LOGGER.warning("RAPT COORDINATOR: Creating BLE device data for device: %s", self._rapt_device_id)
        self.ble_device_data = RAPTPillBluetoothDeviceData(
            hass, f"RAPT Pill {self._rapt_device_id}"
        )
        self.ble_coordinator = PassiveBluetoothProcessorCoordinator(
            hass, 
            _LOGGER, 
            self._rapt_device_id, 
            self.ble_device_data,
            self.ble_device_data._async_handle_bluetooth_data_update
        )
        
        # Start the BLE coordinator to begin receiving data
        _LOGGER.warning("RAPT COORDINATOR: Starting BLE coordinator for device: %s", self._rapt_device_id)
        
        # Register with Home Assistant's Bluetooth system (needed for ESPHome BLE proxies)
        from homeassistant.components.bluetooth import async_register_callback
        
        def ble_callback(service_info: BluetoothServiceInfoBleak, change: str) -> None:
            """Handle Bluetooth updates from ESPHome proxies."""
            _LOGGER.warning("ESPHome BLE CALLBACK: Device %s, Change: %s, Manufacturers: %s", 
                           service_info.address, change, list(service_info.manufacturer_data.keys()))
            if service_info.address == self._rapt_device_id:
                self.ble_device_data._async_handle_bluetooth_data_update(service_info)
        
        # Register callback for our specific device
        self._ble_cancel_callback = async_register_callback(
            hass,
            ble_callback,
            {"address": self._rapt_device_id},
            "advertisement"
        )
        _LOGGER.warning("RAPT COORDINATOR: Registered ESPHome BLE callback for device: %s", self._rapt_device_id)
        
        # Current sensor data from BLE
        self._current_ble_data: Any = None
        
    async def _async_update_data(self) -> RAPTBrewingData:
        """Update data from integrated BLE device."""
        try:
            # Get current BLE sensor data
            self._current_ble_data = self.ble_device_data.get_last_sensor_data()
            
            _LOGGER.debug("RAPT COORDINATOR: Update - BLE data: %s", 
                           self._current_ble_data.to_dict() if self._current_ble_data else "None")
            
            if self._current_ble_data and self.data.current_session:
                # Update current session with new BLE data
                await self._update_current_session_ble(self._current_ble_data)
                
                # Check for alerts
                await self._check_alerts_ble(self._current_ble_data)
                
                # Save data to storage
                await self._save_data()
            elif not self._current_ble_data:
                _LOGGER.debug("RAPT COORDINATOR: No BLE data available")
            elif not self.data.current_session:
                _LOGGER.debug("RAPT COORDINATOR: No current session")
            
            return self.data
            
        except Exception as err:
            raise UpdateFailed(f"Error updating RAPT brewing data: {err}") from err
    
    def get_current_ble_data(self) -> Any:
        """Get current BLE sensor data."""
        return self._current_ble_data
    
    def get_ble_signal_strength(self) -> int | None:
        """Get BLE signal strength."""
        service_info = self.ble_device_data.get_last_service_info()
        return service_info.rssi if service_info else None
    
    async def _update_current_session_ble(self, ble_data: Any) -> None:
        """Update current session with new BLE data."""
        if not self.data.current_session:
            return
            
        session = self.data.current_session
        now = dt_util.now()
        
        # Get signal strength from BLE service info
        signal_strength = self.get_ble_signal_strength()
        
        # Add data point
        data_point = DataPoint(
            timestamp=now,
            gravity=ble_data.gravity,
            temperature=ble_data.temperature,
            battery_level=ble_data.battery,
            signal_strength=signal_strength,
        )
        session.data_points.append(data_point)
        
        # Update current values
        if ble_data.gravity is not None:
            session.current_gravity = ble_data.gravity
            
            # Auto-set original gravity if not set and this is the first gravity reading
            # Use temperature-corrected gravity for more accurate OG measurement
            if session.original_gravity is None and len(session.data_points) <= 1:
                # Apply temperature correction to the raw gravity reading
                corrected_og = self._apply_temp_correction_to_gravity(ble_data.gravity, ble_data.temperature)
                session.original_gravity = corrected_og if corrected_og else ble_data.gravity
                _LOGGER.warning("RAPT AUTO-SET: Original gravity set to %.3f (temp corrected from %.3f) for session: %s", 
                               session.original_gravity, ble_data.gravity, session.name)
                
                # Also set a reasonable default target gravity if not set
                # Typical beer fermentation: OG - 0.020 to 0.030 points
                if session.target_gravity is None:
                    session.target_gravity = max(0.990, ble_data.gravity - 0.025)
                    _LOGGER.warning("RAPT AUTO-SET: Target gravity set to %.3f for session: %s", 
                                   session.target_gravity, session.name)
                
        if ble_data.temperature is not None:
            session.current_temperature = ble_data.temperature
            
        # Calculate derived values
        self._calculate_derived_values(session)
        
        # Limit data points to prevent unlimited growth
        if len(session.data_points) > 10000:
            session.data_points = session.data_points[-10000:]
    
    def _calculate_derived_values(self, session: BrewingSession) -> None:
        """Calculate derived values for the session."""
        # Get temperature-corrected gravity for more accurate calculations
        corrected_gravity = self._get_temperature_corrected_gravity(session)
        
        
        # Calculate alcohol percentage using temperature-corrected gravity with improved accuracy
        if session.original_gravity and corrected_gravity:
            # Validate gravity values are reasonable
            if corrected_gravity >= session.original_gravity:
                session.alcohol_percentage = 0.0  # Fermentation hasn't started
                _LOGGER.debug("RAPT CALC: Alcohol 0.0%% - fermentation not started (CG >= OG)")
            else:
                gravity_drop = session.original_gravity - corrected_gravity
                
                # Apply correction factor based on original gravity for better accuracy
                if session.original_gravity > 1.060:
                    correction_factor = 1.05  # High gravity beers
                elif session.original_gravity > 1.050:
                    correction_factor = 1.02  # Medium gravity beers
                else:
                    correction_factor = 1.0   # Low gravity beers
                
                session.alcohol_percentage = gravity_drop * 131.25 * correction_factor
                
                # Cap at reasonable maximum (20% ABV)
                session.alcohol_percentage = min(session.alcohol_percentage, 20.0)
                
                _LOGGER.debug("RAPT CALC: Alcohol %.1f%% (OG=%.3f, CG_corrected=%.3f, factor=%.2f)", 
                             session.alcohol_percentage, session.original_gravity, corrected_gravity, correction_factor)
        else:
            _LOGGER.warning("RAPT CALC: Cannot calculate alcohol - OG=%s, CG_corrected=%s", 
                           session.original_gravity, corrected_gravity)
        
        # Calculate attenuation using temperature-corrected gravity (FIXED FORMULA)
        if session.original_gravity and corrected_gravity:
            # Proper attenuation formula: (OG - CG) / (OG - 1.000) * 100
            apparent_attenuation = (
                (session.original_gravity - corrected_gravity) /
                (session.original_gravity - 1.000) * 100
            )
            
            session.attenuation = max(0.0, min(100.0, apparent_attenuation))  # Clamp to 0-100%
            _LOGGER.debug("RAPT CALC: Attenuation %.1f%% (OG=%.3f, CG_corrected=%.3f)", 
                         session.attenuation, session.original_gravity, corrected_gravity)
        else:
            _LOGGER.warning("RAPT CALC: Cannot calculate attenuation - OG=%s, CG_corrected=%s", 
                           session.original_gravity, corrected_gravity)
        
        # Calculate fermentation rate using temperature-corrected gravity (FIXED)
        if len(session.data_points) >= 2:
            recent_points = [
                dp for dp in session.data_points[-24:]  # Last 24 data points
                if dp.gravity is not None and dp.temperature is not None
            ]
            if len(recent_points) >= 2:
                time_diff = (recent_points[-1].timestamp - recent_points[0].timestamp).total_seconds() / 3600
                if time_diff > 0:
                    # Apply temperature correction to both points
                    first_corrected = self._apply_temp_correction_to_point(recent_points[0])
                    last_corrected = self._apply_temp_correction_to_point(recent_points[-1])
                    
                    if first_corrected is not None and last_corrected is not None:
                        gravity_diff = last_corrected - first_corrected
                        session.fermentation_rate = gravity_diff / time_diff
    
    def _get_temperature_corrected_gravity(self, session: BrewingSession) -> float | None:
        """Get temperature-corrected gravity for accurate calculations."""
        if not session.current_gravity or not session.current_temperature:
            return None
            
        # Temperature correction formula - remove temperature effects to show actual density
        calibration_temp = 20.0  # °C (reference temperature)
        temp_correction_factor = 0.00013  # per °C (scientific literature)
        
        temp_difference = session.current_temperature - calibration_temp
        thermal_effect = temp_difference * temp_correction_factor
        
        # Remove thermal expansion/contraction effects to get true density
        corrected_gravity = session.current_gravity - thermal_effect
        
        # Safety check: prevent ridiculous temperature corrections
        if abs(thermal_effect) > 0.020:  # Max 20 points correction
            _LOGGER.warning("RAPT TEMP CORRECTION: Extreme correction detected! Raw=%.4f, Temp=%.2f°C, Correction=%.4f - using raw gravity", 
                           session.current_gravity, session.current_temperature, thermal_effect)
            return session.current_gravity
        
        _LOGGER.debug("RAPT TEMP CORRECTION: Raw=%.4f, Temp=%.2f°C, Correction=%.4f, Corrected=%.4f", 
                     session.current_gravity, session.current_temperature, thermal_effect, corrected_gravity)
        
        return corrected_gravity
    
    def _apply_temp_correction_to_point(self, data_point) -> float | None:
        """Apply temperature correction to a single data point."""
        if not data_point.gravity or not data_point.temperature:
            return None
            
        return self._apply_temp_correction_to_gravity(data_point.gravity, data_point.temperature)
    
    def _apply_temp_correction_to_gravity(self, gravity: float, temperature: float) -> float | None:
        """Apply temperature correction to gravity and temperature values."""
        if gravity is None or temperature is None:
            return None
            
        # Temperature correction formula - remove temperature effects to show actual density
        calibration_temp = 20.0  # °C (reference temperature)
        temp_correction_factor = 0.00013  # per °C (scientific literature)
        
        temp_difference = temperature - calibration_temp
        thermal_effect = temp_difference * temp_correction_factor
        
        # Remove thermal expansion/contraction effects to get true density
        corrected_gravity = gravity - thermal_effect
        
        return corrected_gravity
    
    async def _check_alerts_ble(self, ble_data: Any) -> None:
        """Check for brewing alerts using BLE data."""
        if not self.data.current_session:
            return
            
        session = self.data.current_session
        now = dt_util.now()
        
        # Check for stuck fermentation using scientifically accurate threshold
        if session.fermentation_rate is not None and abs(session.fermentation_rate) < FERMENTATION_RATE_STUCK:
            if session.data_points:
                last_significant_change = None
                for dp in reversed(session.data_points):
                    if dp.gravity and abs(dp.gravity - session.current_gravity) > 0.005:
                        last_significant_change = dp.timestamp
                        break
                
                if (last_significant_change and 
                    (now - last_significant_change).total_seconds() > DEFAULT_STUCK_FERMENTATION_HOURS * 3600):
                    await self._add_alert(
                        session,
                        ALERT_TYPE_STUCK_FERMENTATION,
                        "Fermentation appears to be stuck - no gravity change in 48 hours"
                    )
        
        # Check temperature alerts
        if ble_data.temperature is not None:
            if ble_data.temperature > DEFAULT_TEMPERATURE_HIGH_THRESHOLD:
                await self._add_alert(
                    session,
                    ALERT_TYPE_TEMPERATURE_HIGH,
                    f"Temperature too high: {ble_data.temperature:.1f}°C"
                )
            elif ble_data.temperature < DEFAULT_TEMPERATURE_LOW_THRESHOLD:
                await self._add_alert(
                    session,
                    ALERT_TYPE_TEMPERATURE_LOW,
                    f"Temperature too low: {ble_data.temperature:.1f}°C"
                )
        
        # Check for fermentation completion
        if (session.target_gravity and session.current_gravity and 
            session.current_gravity <= session.target_gravity + 0.002):
            await self._add_alert(
                session,
                ALERT_TYPE_FERMENTATION_COMPLETE,
                "Fermentation appears to be complete"
            )
        
        # Check battery level - but only warn if battery has been calibrated
        if ble_data.battery is not None:
            # Mark battery as calibrated if we see any reading above 0% (not stuck at 0%)
            if ble_data.battery > 0 and not session.battery_calibrated:
                session.battery_calibrated = True
                _LOGGER.info("RAPT BATTERY: Battery calibrated at %.0f%% for session: %s", 
                           ble_data.battery, session.name)
            
            # Only warn about low battery if it's been calibrated (prevents 0% startup warnings)
            if (session.battery_calibrated and 
                ble_data.battery < DEFAULT_LOW_BATTERY_THRESHOLD):
                await self._add_alert(
                    session,
                    ALERT_TYPE_LOW_BATTERY,
                    f"Low battery: {ble_data.battery}%"
                )
    
    async def _add_alert(self, session: BrewingSession, alert_type: str, message: str) -> None:
        """Add an alert to the session."""
        now = dt_util.now()
        
        # For stuck fermentation, only alert once per session (not recurring)
        if alert_type == ALERT_TYPE_STUCK_FERMENTATION:
            existing_stuck_alerts = [
                alert for alert in session.alerts
                if alert.type == ALERT_TYPE_STUCK_FERMENTATION
            ]
            if existing_stuck_alerts:
                _LOGGER.debug("RAPT ALERT SKIPPED: Stuck fermentation already alerted for session: %s", session.name)
                return
        else:
            # For other alerts, check if similar alert already exists (within last hour)
            recent_alerts = [
                alert for alert in session.alerts
                if (alert.type == alert_type and 
                    (now - alert.timestamp).total_seconds() < 3600)
            ]
            if recent_alerts:
                _LOGGER.debug("RAPT ALERT SKIPPED (recent duplicate): Type=%s, Message=%s", 
                             alert_type, message)
                return
        
        # If we get here, we should create the alert
        alert = Alert(
            type=alert_type,
            message=message,
            timestamp=now,
        )
        session.alerts.append(alert)
        
        _LOGGER.warning("RAPT ALERT TRIGGERED: Type=%s, Message=%s, Session=%s", 
                       alert_type, message, session.name)
        
        # Send Home Assistant persistent notification
        try:
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "message": message,
                    "title": f"RAPT Brewing Alert - {session.name}",
                    "notification_id": f"rapt_brewing_{alert_type}_{session.id}",
                },
            )
        except Exception as e:
            _LOGGER.warning("RAPT ALERT: Failed to send persistent notification: %s", e)
        
        # Send external notification if configured
        notification_service = self.entry.options.get(CONF_NOTIFICATION_SERVICE)
        if notification_service and notification_service.strip():
            try:
                # Parse service domain and name
                service_parts = notification_service.split(".", 1)
                if len(service_parts) == 2:
                    domain, service_name = service_parts
                    
                    await self.hass.services.async_call(
                        domain,
                        service_name,
                        {
                            "title": f"🍺 RAPT Brewing Alert - {session.name}",
                            "message": message,
                            "data": {
                                "tag": "rapt_brewing",
                                "group": "brewing",
                                "alert_type": alert_type,
                                "session_name": session.name,
                                "session_id": session.id,
                            }
                        },
                    )
                    _LOGGER.info("RAPT ALERT: Sent external notification via %s", notification_service)
                else:
                    _LOGGER.warning("RAPT ALERT: Invalid notification service format: %s", notification_service)
            except Exception as e:
                _LOGGER.warning("RAPT ALERT: Failed to send external notification via %s: %s", notification_service, e)
        
        _LOGGER.warning("RAPT ALERT NOTIFICATION SENT: %s", message)
    
    async def start_session(self, name: str, recipe: str | None = None, 
                          original_gravity: float | None = None,
                          target_gravity: float | None = None,
                          target_temperature: float | None = None) -> str:
        """Start a new brewing session."""
        session_id = f"session_{dt_util.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = BrewingSession(
            id=session_id,
            name=name,
            recipe=recipe,
            original_gravity=original_gravity,
            target_gravity=target_gravity,
            target_temperature=target_temperature,
            state=SESSION_STATE_ACTIVE,
            started_at=dt_util.now(),
        )
        
        self.data.add_session(session)
        self.data.set_current_session(session_id)
        
        # Reset sensor values to create a clean break in history graphs
        await self._reset_sensor_values()
        
        await self._save_data()
        return session_id
    
    async def _reset_sensor_values(self) -> None:
        """Reset sensor values to create a clean break in history graphs when starting a new session."""
        if not self.data.current_session:
            return
        
        session = self.data.current_session
        
        # Temporarily clear current values to create a gap in the history
        session.current_gravity = None
        session.current_temperature = None
        session.alcohol_percentage = None
        session.attenuation = None
        session.fermentation_rate = None
        
        # Clear data points to start fresh
        session.data_points = []
        session.alerts = []
        
        # Trigger a coordinator update to push None values to sensors
        await self.async_request_refresh()
        
        _LOGGER.info("RAPT SESSION: Reset sensor values for new session: %s", session.name)
    
    async def stop_session(self, session_id: str) -> None:
        """Stop a brewing session."""
        session = self.data.get_session(session_id)
        if session:
            session.state = SESSION_STATE_IDLE
            session.completed_at = dt_util.now()
            
            if self.data.current_session and self.data.current_session.id == session_id:
                self.data.set_current_session(None)
            
            await self._save_data()
    
    async def delete_session(self, session_id: str) -> None:
        """Delete a brewing session."""
        if self.data.current_session and self.data.current_session.id == session_id:
            self.data.set_current_session(None)
        
        self.data.remove_session(session_id)
        await self._save_data()
    
    async def _save_data(self) -> None:
        """Save data to storage."""
        data_to_save = {
            "sessions": {
                session_id: session.to_dict()
                for session_id, session in self.data.sessions.items()
            },
            "current_session_id": self.data.current_session.id if self.data.current_session else None,
            "settings": self.data.settings,
        }
        
        await self.store.async_save(data_to_save)
    
    async def _load_data(self) -> None:
        """Load data from storage."""
        stored_data = await self.store.async_load()
        
        if stored_data:
            # Load sessions
            for session_id, session_data in stored_data.get("sessions", {}).items():
                session = BrewingSession.from_dict(session_data)
                self.data.add_session(session)
            
            # Set current session
            current_session_id = stored_data.get("current_session_id")
            if current_session_id:
                self.data.set_current_session(current_session_id)
            
            # Load settings
            self.data.settings = stored_data.get("settings", {})
    
    async def async_config_entry_first_refresh(self) -> None:
        """Perform first refresh."""
        await self._load_data()
        await super().async_config_entry_first_refresh()
    
    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        if self._ble_cancel_callback:
            self._ble_cancel_callback()
            self._ble_cancel_callback = None
        await super().async_shutdown()
    
    @staticmethod
    def _safe_float(value: Any) -> float | None:
        """Safely convert value to float."""
        if value is None or value == "unavailable" or value == "unknown":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _safe_int(value: Any) -> int | None:
        """Safely convert value to int."""
        if value is None or value == "unavailable" or value == "unknown":
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None