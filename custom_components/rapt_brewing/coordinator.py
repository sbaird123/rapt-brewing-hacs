"""Coordinator for RAPT Brewing integration."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    CONF_RAPT_DEVICE_ID,
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
        
    async def _async_update_data(self) -> RAPTBrewingData:
        """Update data from RAPT BLE integration."""
        try:
            # Get data from RAPT BLE integration
            rapt_data = await self._get_rapt_ble_data()
            
            if rapt_data and self.data.current_session:
                # Update current session with new data
                await self._update_current_session(rapt_data)
                
                # Check for alerts
                await self._check_alerts(rapt_data)
                
                # Save data to storage
                await self._save_data()
            
            return self.data
            
        except Exception as err:
            raise UpdateFailed(f"Error updating RAPT brewing data: {err}") from err
    
    async def _get_rapt_ble_data(self) -> dict[str, Any] | None:
        """Get current data from RAPT BLE integration."""
        if not self._rapt_device_id:
            return None
            
        # Get the RAPT BLE device state
        entity_registry: EntityRegistry = self.hass.helpers.entity_registry.async_get(self.hass)
        
        # Find RAPT BLE entities for this device
        rapt_entities = {}
        for entity_id, entry in entity_registry.entities.items():
            if (entry.platform == "rapt_ble" and 
                entity_id.startswith(f"sensor.{self._rapt_device_id}")):
                state = self.hass.states.get(entity_id)
                if state:
                    sensor_type = entity_id.split(".")[-1]
                    rapt_entities[sensor_type] = state.state
        
        return rapt_entities if rapt_entities else None
    
    async def _update_current_session(self, rapt_data: dict[str, Any]) -> None:
        """Update current session with new RAPT data."""
        if not self.data.current_session:
            return
            
        session = self.data.current_session
        now = datetime.now()
        
        # Extract sensor values
        gravity = self._safe_float(rapt_data.get("specific_gravity"))
        temperature = self._safe_float(rapt_data.get("temperature"))
        battery = self._safe_int(rapt_data.get("battery"))
        signal = self._safe_int(rapt_data.get("signal_strength"))
        
        # Add data point
        data_point = DataPoint(
            timestamp=now,
            gravity=gravity,
            temperature=temperature,
            battery_level=battery,
            signal_strength=signal,
        )
        session.data_points.append(data_point)
        
        # Update current values
        if gravity is not None:
            session.current_gravity = gravity
        if temperature is not None:
            session.current_temperature = temperature
            
        # Calculate derived values
        self._calculate_derived_values(session)
        
        # Limit data points to prevent unlimited growth
        if len(session.data_points) > 10000:
            session.data_points = session.data_points[-10000:]
    
    def _calculate_derived_values(self, session: BrewingSession) -> None:
        """Calculate derived values for the session."""
        # Calculate alcohol percentage
        if session.original_gravity and session.current_gravity:
            session.alcohol_percentage = (
                (session.original_gravity - session.current_gravity) * 131.25
            )
        
        # Calculate attenuation
        if session.original_gravity and session.current_gravity and session.target_gravity:
            apparent_attenuation = (
                (session.original_gravity - session.current_gravity) /
                (session.original_gravity - session.target_gravity) * 100
            )
            session.attenuation = apparent_attenuation
        
        # Calculate fermentation rate (gravity change per hour)
        if len(session.data_points) >= 2:
            recent_points = [
                dp for dp in session.data_points[-24:]  # Last 24 data points
                if dp.gravity is not None
            ]
            if len(recent_points) >= 2:
                time_diff = (recent_points[-1].timestamp - recent_points[0].timestamp).total_seconds() / 3600
                if time_diff > 0:
                    gravity_diff = recent_points[-1].gravity - recent_points[0].gravity
                    session.fermentation_rate = gravity_diff / time_diff
    
    async def _check_alerts(self, rapt_data: dict[str, Any]) -> None:
        """Check for brewing alerts."""
        if not self.data.current_session:
            return
            
        session = self.data.current_session
        now = datetime.now()
        
        # Check for stuck fermentation
        if session.fermentation_rate is not None and abs(session.fermentation_rate) < 0.001:
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
        if session.current_temperature is not None:
            if session.current_temperature > DEFAULT_TEMPERATURE_HIGH_THRESHOLD:
                await self._add_alert(
                    session,
                    ALERT_TYPE_TEMPERATURE_HIGH,
                    f"Temperature too high: {session.current_temperature}°C"
                )
            elif session.current_temperature < DEFAULT_TEMPERATURE_LOW_THRESHOLD:
                await self._add_alert(
                    session,
                    ALERT_TYPE_TEMPERATURE_LOW,
                    f"Temperature too low: {session.current_temperature}°C"
                )
        
        # Check for fermentation completion
        if (session.target_gravity and session.current_gravity and 
            session.current_gravity <= session.target_gravity + 0.002):
            await self._add_alert(
                session,
                ALERT_TYPE_FERMENTATION_COMPLETE,
                "Fermentation appears to be complete"
            )
        
        # Check battery level
        battery = self._safe_int(rapt_data.get("battery"))
        if battery is not None and battery < DEFAULT_LOW_BATTERY_THRESHOLD:
            await self._add_alert(
                session,
                ALERT_TYPE_LOW_BATTERY,
                f"Low battery: {battery}%"
            )
    
    async def _add_alert(self, session: BrewingSession, alert_type: str, message: str) -> None:
        """Add an alert to the session."""
        # Check if similar alert already exists (within last hour)
        now = datetime.now()
        recent_alerts = [
            alert for alert in session.alerts
            if (alert.type == alert_type and 
                (now - alert.timestamp).total_seconds() < 3600)
        ]
        
        if not recent_alerts:
            alert = Alert(
                type=alert_type,
                message=message,
                timestamp=now,
            )
            session.alerts.append(alert)
            
            # Send Home Assistant notification
            await self.hass.services.async_call(
                "notify",
                "persistent_notification",
                {
                    "message": message,
                    "title": f"RAPT Brewing Alert - {session.name}",
                    "notification_id": f"rapt_brewing_{alert_type}_{session.id}",
                },
            )
    
    async def start_session(self, name: str, recipe: str | None = None, 
                          original_gravity: float | None = None,
                          target_gravity: float | None = None,
                          target_temperature: float | None = None) -> str:
        """Start a new brewing session."""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = BrewingSession(
            id=session_id,
            name=name,
            recipe=recipe,
            original_gravity=original_gravity,
            target_gravity=target_gravity,
            target_temperature=target_temperature,
            state=SESSION_STATE_ACTIVE,
            started_at=datetime.now(),
        )
        
        self.data.add_session(session)
        self.data.set_current_session(session_id)
        
        await self._save_data()
        return session_id
    
    async def stop_session(self, session_id: str) -> None:
        """Stop a brewing session."""
        session = self.data.get_session(session_id)
        if session:
            session.state = SESSION_STATE_IDLE
            session.completed_at = datetime.now()
            
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