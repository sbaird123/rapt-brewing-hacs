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
            
            if self._current_ble_data and self.data.current_session:
                # Update current session with new BLE data
                await self._update_current_session_ble(self._current_ble_data)
                
                # Check for alerts
                await self._check_alerts_ble(self._current_ble_data)
                
                # Save data to storage
                await self._save_data()
            
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
        now = datetime.now()
        
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
        if ble_data.temperature is not None:
            session.current_temperature = ble_data.temperature
            
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
    
    async def _check_alerts_ble(self, ble_data: Any) -> None:
        """Check for brewing alerts using BLE data."""
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
        
        # Check battery level
        if ble_data.battery is not None and ble_data.battery < DEFAULT_LOW_BATTERY_THRESHOLD:
            await self._add_alert(
                session,
                ALERT_TYPE_LOW_BATTERY,
                f"Low battery: {ble_data.battery}%"
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