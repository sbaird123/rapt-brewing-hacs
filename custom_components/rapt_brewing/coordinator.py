"""Coordinator for RAPT Brewing integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
import homeassistant.util.dt as dt_util
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Event, EventStateChangedData, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    CLOUD_SCAN_INTERVAL,
    CONF_RAPT_DEVICE_ID,
    CONF_NOTIFICATION_SERVICE,
    CONF_SOURCE_TYPE,
    CONF_GRAVITY_ENTITY,
    CONF_TEMPERATURE_ENTITY,
    CONF_BATTERY_ENTITY,
    CONF_SIGNAL_ENTITY,
    CONF_API_EMAIL,
    CONF_API_SECRET,
    CONF_HYDROMETER_ID,
    CONF_STUCK_FERMENTATION_HOURS,
    CONF_TEMPERATURE_HIGH_THRESHOLD,
    CONF_TEMPERATURE_LOW_THRESHOLD,
    CONF_LOW_BATTERY_THRESHOLD,
    CONF_OFFLINE_TIMEOUT_MINUTES,
    CONF_GRAVITY_OFFSET,
    CONF_TEMPERATURE_OFFSET,
    CONF_GRAVITY_UNIT,
    GRAVITY_UNIT_SG,
    SOURCE_TYPE_BLUETOOTH,
    SOURCE_TYPE_ENTITY,
    SOURCE_TYPE_CLOUD,
    SESSION_STATE_ACTIVE,
    SESSION_STATE_IDLE,
    ALERT_TYPE_STUCK_FERMENTATION,
    ALERT_TYPE_TEMPERATURE_HIGH,
    ALERT_TYPE_TEMPERATURE_LOW,
    ALERT_TYPE_FERMENTATION_COMPLETE,
    ALERT_TYPE_LOW_BATTERY,
    ALERT_TYPE_HEATER_INEFFECTIVE,
    DEFAULT_STUCK_FERMENTATION_HOURS,
    DEFAULT_TEMPERATURE_HIGH_THRESHOLD,
    DEFAULT_TEMPERATURE_LOW_THRESHOLD,
    DEFAULT_LOW_BATTERY_THRESHOLD,
    DEFAULT_OFFLINE_TIMEOUT_MINUTES,
    DEFAULT_OFFLINE_TIMEOUT_MINUTES_CLOUD,
    EVENT_RAPT_BREWING_ALERT,
    FERMENTATION_RATE_STUCK,
    GRAVITY_MIN,
    GRAVITY_MAX,
    TEMPERATURE_MIN,
    TEMPERATURE_MAX,
    BATTERY_MIN,
    BATTERY_MAX,
)
from .data import RAPTBrewingData, BrewingSession, DataPoint, Alert, downsample_data_points

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
LEGACY_STORAGE_KEY = "rapt_brewing_sessions"
SAVE_DELAY_SECONDS = 30
MAX_DATA_POINTS = 10000
DOWNSAMPLE_TRIGGER = 2000

# Alerts that should fire at most once per session instead of re-notifying
# every time the deduplication window expires.
ONCE_PER_SESSION_ALERTS = {
    ALERT_TYPE_STUCK_FERMENTATION,
    ALERT_TYPE_FERMENTATION_COMPLETE,
    ALERT_TYPE_HEATER_INEFFECTIVE,
}


class RAPTBrewingCoordinator(DataUpdateCoordinator[RAPTBrewingData]):
    """Coordinator for RAPT Brewing integration."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.source_type = entry.data.get(CONF_SOURCE_TYPE, SOURCE_TYPE_BLUETOOTH)
        scan_interval = (
            CLOUD_SCAN_INTERVAL if self.source_type == SOURCE_TYPE_CLOUD
            else DEFAULT_SCAN_INTERVAL
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.entry = entry
        # Storage is scoped per config entry so multiple entries (e.g. two
        # Pills) don't clobber each other's sessions.
        self.store = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
        self.data = RAPTBrewingData()
        self._rapt_device_id = entry.data.get(CONF_RAPT_DEVICE_ID)
        if self._rapt_device_id:
            self._rapt_device_id = self._rapt_device_id.upper()
        self._ble_cancel_callback = None
        self._entity_cancel_callback = None
        self._signal_strength: int | None = None
        self.ble_device_data = None
        self._cloud_client = None
        self._last_ingested_at: datetime | None = None
        self._started_at: datetime = dt_util.utcnow()
        self.last_data_received: datetime | None = None

        # Current sensor data (BLE, entity or cloud derived)
        self._current_ble_data: Any = None

        if self.source_type == SOURCE_TYPE_ENTITY:
            self._setup_entity_source()
        elif self.source_type == SOURCE_TYPE_CLOUD:
            self._setup_cloud_source()
        else:
            self._setup_bluetooth_source(hass)

    # ------------------------------------------------------------------
    # Options helpers
    # ------------------------------------------------------------------

    def _opt(self, key: str, default: Any) -> Any:
        """Read an option with a default."""
        return self.entry.options.get(key, default)

    @property
    def stuck_fermentation_hours(self) -> float:
        """Configured stuck-fermentation alert window in hours."""
        return float(self._opt(CONF_STUCK_FERMENTATION_HOURS, DEFAULT_STUCK_FERMENTATION_HOURS))

    @property
    def temperature_high_threshold(self) -> float:
        """Configured high-temperature alert threshold (°C)."""
        return float(self._opt(CONF_TEMPERATURE_HIGH_THRESHOLD, DEFAULT_TEMPERATURE_HIGH_THRESHOLD))

    @property
    def temperature_low_threshold(self) -> float:
        """Configured low-temperature alert threshold (°C)."""
        return float(self._opt(CONF_TEMPERATURE_LOW_THRESHOLD, DEFAULT_TEMPERATURE_LOW_THRESHOLD))

    @property
    def low_battery_threshold(self) -> int:
        """Configured low-battery alert threshold (%)."""
        return int(self._opt(CONF_LOW_BATTERY_THRESHOLD, DEFAULT_LOW_BATTERY_THRESHOLD))

    @property
    def offline_timeout(self) -> timedelta:
        """How long without fresh data before the device is considered offline."""
        default = (
            DEFAULT_OFFLINE_TIMEOUT_MINUTES_CLOUD
            if self.source_type == SOURCE_TYPE_CLOUD
            else DEFAULT_OFFLINE_TIMEOUT_MINUTES
        )
        return timedelta(minutes=float(self._opt(CONF_OFFLINE_TIMEOUT_MINUTES, default)))

    @property
    def gravity_offset(self) -> float:
        """Calibration offset added to raw gravity readings (SG)."""
        return float(self._opt(CONF_GRAVITY_OFFSET, 0.0))

    @property
    def temperature_offset(self) -> float:
        """Calibration offset added to raw temperature readings (°C)."""
        return float(self._opt(CONF_TEMPERATURE_OFFSET, 0.0))

    @property
    def gravity_unit(self) -> str:
        """Configured gravity display unit (sg or plato)."""
        return self._opt(CONF_GRAVITY_UNIT, GRAVITY_UNIT_SG)

    @property
    def is_online(self) -> bool:
        """Return True if fresh data has been received within the offline timeout."""
        reference = self.last_data_received or self._started_at
        return dt_util.utcnow() - reference < self.offline_timeout

    # ------------------------------------------------------------------
    # Data sources
    # ------------------------------------------------------------------

    def _setup_bluetooth_source(self, hass: HomeAssistant) -> None:
        """Wire up direct Bluetooth data ingestion."""
        from homeassistant.components.bluetooth import (
            BluetoothScanningMode,
            async_register_callback,
        )
        from .ble_device import RAPTPillBluetoothDeviceData

        _LOGGER.debug("RAPT COORDINATOR: Creating BLE device data for device: %s", self._rapt_device_id)
        self.ble_device_data = RAPTPillBluetoothDeviceData(
            f"RAPT Pill {self._rapt_device_id}"
        )

        @callback
        def ble_callback(service_info: BluetoothServiceInfoBleak, change: str) -> None:
            _LOGGER.debug("RAPT BLE CALLBACK: Device %s, Change: %s, Manufacturers: %s",
                          service_info.address, change, list(service_info.manufacturer_data.keys()))
            self.ble_device_data.handle_advertisement(service_info)

        self._ble_cancel_callback = async_register_callback(
            hass,
            ble_callback,
            {"address": self._rapt_device_id},
            BluetoothScanningMode.ACTIVE,
        )
        _LOGGER.debug("RAPT COORDINATOR: Registered BLE callback for device: %s", self._rapt_device_id)

    def _setup_entity_source(self) -> None:
        """Wire up HA entity-based data ingestion."""
        tracked = [
            eid for eid in (
                self.entry.data.get(CONF_GRAVITY_ENTITY),
                self.entry.data.get(CONF_TEMPERATURE_ENTITY),
                self.entry.data.get(CONF_BATTERY_ENTITY),
                self.entry.data.get(CONF_SIGNAL_ENTITY),
            )
            if eid
        ]
        _LOGGER.debug("RAPT COORDINATOR: Entity source tracking: %s", tracked)

        @callback
        def _handle_entity_change(event: Event[EventStateChangedData]) -> None:
            self._refresh_from_entities()
            self.hass.async_create_task(self.async_request_refresh())

        self._entity_cancel_callback = async_track_state_change_event(
            self.hass, tracked, _handle_entity_change
        )

    def _setup_cloud_source(self) -> None:
        """Wire up RAPT cloud data ingestion."""
        from homeassistant.helpers import aiohttp_client
        from .api import RAPTCloudClient

        self._cloud_client = RAPTCloudClient(
            aiohttp_client.async_get_clientsession(self.hass),
            self.entry.data[CONF_API_EMAIL],
            self.entry.data[CONF_API_SECRET],
        )
        _LOGGER.debug("RAPT COORDINATOR: Cloud source configured for hydrometer %s",
                      self.entry.data.get(CONF_HYDROMETER_ID))

    def _refresh_from_entities(self) -> None:
        """Build sensor data from the configured HA entities."""
        from .ble_device import RAPTPillSensorData

        gravity = self._safe_float(
            self._get_entity_state(self.entry.data.get(CONF_GRAVITY_ENTITY))
        )
        temperature = self._safe_float(
            self._get_entity_state(self.entry.data.get(CONF_TEMPERATURE_ENTITY))
        )
        battery = self._safe_int(
            self._get_entity_state(self.entry.data.get(CONF_BATTERY_ENTITY))
        )
        signal = self._safe_int(
            self._get_entity_state(self.entry.data.get(CONF_SIGNAL_ENTITY))
        )

        if gravity is None and temperature is None and battery is None:
            self._current_ble_data = None
            self._signal_strength = signal
            return

        self._current_ble_data = RAPTPillSensorData(
            temperature=temperature,
            gravity=gravity,
            battery=battery,
            signal_strength=signal,
        )
        self._signal_strength = signal

    async def _refresh_from_cloud(self) -> bool:
        """Fetch the latest cloud telemetry; returns True if data is new."""
        from .api import RAPTCloudAuthError, RAPTCloudError
        from .ble_device import RAPTPillSensorData

        hydrometer_id = self.entry.data[CONF_HYDROMETER_ID]
        try:
            record = await self._cloud_client.async_get_latest_telemetry(hydrometer_id)
        except RAPTCloudAuthError as err:
            raise UpdateFailed(f"RAPT cloud authentication failed: {err}") from err
        except RAPTCloudError as err:
            raise UpdateFailed(f"RAPT cloud error: {err}") from err

        if record is None:
            _LOGGER.debug("RAPT CLOUD: No telemetry in the last 24h for %s", hydrometer_id)
            self._current_ble_data = None
            return False

        self._current_ble_data = RAPTPillSensorData(
            temperature=record["temperature"],
            gravity=record["gravity"],
            battery=record["battery"],
            signal_strength=record["signal_strength"],
        )
        self._signal_strength = record["signal_strength"]

        created_on = record.get("created_on")
        if created_on is not None and created_on == self._last_ingested_at:
            return False
        self._last_ingested_at = created_on or dt_util.utcnow()
        return True

    def _get_entity_state(self, entity_id: str | None) -> Any:
        """Read the current state value of an entity."""
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        return state.state if state else None

    # ------------------------------------------------------------------
    # Validation and calibration
    # ------------------------------------------------------------------

    def _validate_gravity(self, value: float | None) -> float | None:
        """Reject implausible gravity readings before they reach session state."""
        if value is None:
            return None
        if GRAVITY_MIN <= value <= GRAVITY_MAX:
            return value
        _LOGGER.warning("RAPT FILTER: Rejecting out-of-range gravity %.4f (allowed %.3f–%.3f)",
                       value, GRAVITY_MIN, GRAVITY_MAX)
        return None

    def _validate_temperature(self, value: float | None) -> float | None:
        """Reject implausible temperature readings."""
        if value is None:
            return None
        if TEMPERATURE_MIN <= value <= TEMPERATURE_MAX:
            return value
        _LOGGER.warning("RAPT FILTER: Rejecting out-of-range temperature %.2f°C (allowed %.1f–%.1f)",
                       value, TEMPERATURE_MIN, TEMPERATURE_MAX)
        return None

    def _validate_battery(self, value: int | None) -> int | None:
        """Reject implausible battery readings."""
        if value is None:
            return None
        if BATTERY_MIN <= value <= BATTERY_MAX:
            return value
        _LOGGER.warning("RAPT FILTER: Rejecting out-of-range battery %d%% (allowed %d–%d)",
                       value, BATTERY_MIN, BATTERY_MAX)
        return None

    def _calibrated_readings(self, ble_data: Any) -> tuple[float | None, float | None, int | None]:
        """Apply calibration offsets and validation to raw readings."""
        gravity = ble_data.gravity
        if gravity is not None:
            gravity = gravity + self.gravity_offset
        temperature = ble_data.temperature
        if temperature is not None:
            temperature = temperature + self.temperature_offset
        return (
            self._validate_gravity(gravity),
            self._validate_temperature(temperature),
            self._validate_battery(ble_data.battery),
        )

    # ------------------------------------------------------------------
    # Update cycle
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> RAPTBrewingData:
        """Update data from the configured source."""
        try:
            if self.source_type == SOURCE_TYPE_ENTITY:
                self._refresh_from_entities()
                has_new_data = self._current_ble_data is not None
            elif self.source_type == SOURCE_TYPE_CLOUD:
                has_new_data = await self._refresh_from_cloud()
            else:
                self._current_ble_data = self.ble_device_data.get_last_sensor_data()
                # Only treat the reading as new if a fresh advertisement was
                # parsed since the last update; otherwise we would re-ingest
                # the same stale reading forever after the Pill goes offline.
                last_telemetry = self.ble_device_data.last_telemetry_at
                has_new_data = (
                    self._current_ble_data is not None
                    and last_telemetry is not None
                    and last_telemetry != self._last_ingested_at
                )
                if has_new_data:
                    self._last_ingested_at = last_telemetry

            _LOGGER.debug("RAPT COORDINATOR: Update - data: %s, new: %s",
                          self._current_ble_data.to_dict() if self._current_ble_data else "None",
                          has_new_data)

            if has_new_data:
                self.last_data_received = dt_util.utcnow()
                # Ingest into every active session (normally just one), not
                # only the currently *viewed* session, so browsing history
                # doesn't interrupt a running fermentation.
                active_sessions = [
                    s for s in self.data.sessions.values()
                    if s.state == SESSION_STATE_ACTIVE
                ]
                for session in active_sessions:
                    await self._ingest_data(session, self._current_ble_data)
                    await self._check_alerts(session, self._current_ble_data)

                if active_sessions:
                    # Save data to storage (delayed, to limit disk writes)
                    self._schedule_save()

            return self.data

        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Error updating RAPT brewing data: {err}") from err

    def get_current_ble_data(self) -> Any:
        """Get current BLE sensor data."""
        return self._current_ble_data

    def get_ble_signal_strength(self) -> int | None:
        """Get BLE signal strength."""
        if self.source_type in (SOURCE_TYPE_ENTITY, SOURCE_TYPE_CLOUD):
            return self._signal_strength
        service_info = self.ble_device_data.get_last_service_info()
        return service_info.rssi if service_info else None

    async def _ingest_data(self, session: BrewingSession, ble_data: Any) -> None:
        """Add new sensor data to a brewing session."""
        gravity, temperature, battery = self._calibrated_readings(ble_data)

        now = dt_util.now()

        # Get signal strength from BLE service info
        signal_strength = self.get_ble_signal_strength()

        # Add data point (only fields that passed validation; bad readings stored as None)
        data_point = DataPoint(
            timestamp=now,
            gravity=gravity,
            temperature=temperature,
            battery_level=battery,
            signal_strength=signal_strength,
            gravity_velocity=ble_data.gravity_velocity,
            accelerometer_x=ble_data.accelerometer_x,
            accelerometer_y=ble_data.accelerometer_y,
            accelerometer_z=ble_data.accelerometer_z,
        )
        session.data_points.append(data_point)

        # Update current values
        if gravity is not None:
            session.current_gravity = gravity

            # Auto-set original gravity if not set and this is the first gravity reading
            # Use temperature-corrected gravity for more accurate OG measurement
            if session.original_gravity is None and len(session.data_points) <= 1:
                corrected_og = self._apply_temp_correction_to_gravity(gravity, temperature)
                session.original_gravity = corrected_og if corrected_og is not None else gravity
                _LOGGER.info("RAPT AUTO-SET: Original gravity set to %.3f (temp corrected from %.3f) for session: %s",
                             session.original_gravity, gravity, session.name)

                # Also set a reasonable default target gravity if not set
                # Typical beer fermentation: OG - 0.020 to 0.030 points
                if session.target_gravity is None:
                    session.target_gravity = max(0.990, gravity - 0.025)
                    _LOGGER.info("RAPT AUTO-SET: Target gravity set to %.3f for session: %s",
                                 session.target_gravity, session.name)

        if temperature is not None:
            session.current_temperature = temperature

        # Calculate derived values
        self._calculate_derived_values(session)

        # Thin out old data points, then enforce the hard cap
        if len(session.data_points) >= DOWNSAMPLE_TRIGGER:
            session.data_points = downsample_data_points(session.data_points, now)
        if len(session.data_points) > MAX_DATA_POINTS:
            session.data_points = session.data_points[-MAX_DATA_POINTS:]

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
            _LOGGER.debug("RAPT CALC: Cannot calculate alcohol - OG=%s, CG_corrected=%s",
                          session.original_gravity, corrected_gravity)

        # Calculate attenuation using temperature-corrected gravity
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
            _LOGGER.debug("RAPT CALC: Cannot calculate attenuation - OG=%s, CG_corrected=%s",
                          session.original_gravity, corrected_gravity)

        # Fermentation rate: prefer the Pill's officially computed gravity
        # velocity (points/day, v2 firmware) over our own two-point estimate.
        official_velocity = None
        for dp in reversed(session.data_points[-5:]):
            if dp.gravity_velocity is not None:
                official_velocity = dp.gravity_velocity
                break

        if official_velocity is not None:
            # points/day → SG/hour (1 point = 0.001 SG)
            session.fermentation_rate = official_velocity / 1000.0 / 24.0
        elif len(session.data_points) >= 2:
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
        if session.current_gravity is None or session.current_temperature is None:
            return None
        return self._apply_temp_correction_to_gravity(
            session.current_gravity, session.current_temperature
        )

    def _apply_temp_correction_to_point(self, data_point: DataPoint) -> float | None:
        """Apply temperature correction to a single data point."""
        if data_point.gravity is None or data_point.temperature is None:
            return None

        return self._apply_temp_correction_to_gravity(data_point.gravity, data_point.temperature)

    def _apply_temp_correction_to_gravity(self, gravity: float | None, temperature: float | None) -> float | None:
        """Apply temperature correction to a gravity reading."""
        if gravity is None or temperature is None:
            return None

        # Temperature correction formula - remove temperature effects to show actual density
        calibration_temp = 20.0  # °C (reference temperature)
        temp_correction_factor = 0.00013  # per °C (scientific literature)

        temp_difference = temperature - calibration_temp
        thermal_effect = temp_difference * temp_correction_factor

        # Safety check: prevent ridiculous temperature corrections
        if abs(thermal_effect) > 0.020:  # Max 20 points correction
            _LOGGER.warning("RAPT TEMP CORRECTION: Extreme correction detected! Raw=%.4f, Temp=%.2f°C, Correction=%.4f - using raw gravity",
                            gravity, temperature, thermal_effect)
            return gravity

        # Remove thermal expansion/contraction effects to get true density
        return gravity - thermal_effect

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------

    async def _check_alerts(self, session: BrewingSession, ble_data: Any) -> None:
        """Check for brewing alerts on a session using new sensor data."""
        now = dt_util.now()

        # Use calibrated + validated readings so a garbage spike rejected
        # from the session can't trigger alerts either.
        _gravity, temperature, battery = self._calibrated_readings(ble_data)

        # Check for stuck fermentation using scientifically accurate threshold
        if (session.fermentation_rate is not None
                and abs(session.fermentation_rate) < FERMENTATION_RATE_STUCK
                and session.current_gravity is not None
                and session.data_points):
            last_significant_change = None
            for dp in reversed(session.data_points):
                if dp.gravity is not None and abs(dp.gravity - session.current_gravity) > 0.005:
                    last_significant_change = dp.timestamp
                    break

            if last_significant_change is None:
                # Gravity never changed significantly - measure from session start
                last_significant_change = session.data_points[0].timestamp

            stuck_hours = self.stuck_fermentation_hours
            if (now - last_significant_change).total_seconds() > stuck_hours * 3600:
                await self.async_add_alert(
                    session,
                    ALERT_TYPE_STUCK_FERMENTATION,
                    f"Fermentation appears to be stuck - no gravity change in {stuck_hours:g} hours"
                )

        # Check temperature alerts - only alert when conditions are concerning
        if temperature is not None:
            # Hot temperature during active fermentation is concerning
            if temperature > self.temperature_high_threshold:
                await self.async_add_alert(
                    session,
                    ALERT_TYPE_TEMPERATURE_HIGH,
                    f"Temperature too high: {temperature:.1f}°C"
                )
            # Cold temperature alert only if fermentation isn't near completion (cold crash expected)
            elif temperature < self.temperature_low_threshold:
                # Only alert if attenuation < 70% (early/mid fermentation)
                # Cold crash at 70%+ attenuation is expected and normal
                if session.attenuation is None or session.attenuation < 70.0:
                    await self.async_add_alert(
                        session,
                        ALERT_TYPE_TEMPERATURE_LOW,
                        f"Temperature too low during fermentation: {temperature:.1f}°C"
                    )

        # Check for fermentation completion
        if (session.target_gravity and session.current_gravity and
            session.current_gravity <= session.target_gravity + 0.002):
            await self.async_add_alert(
                session,
                ALERT_TYPE_FERMENTATION_COMPLETE,
                "Fermentation appears to be complete"
            )

        # Check battery level - but only warn if battery has been calibrated
        if battery is not None:
            # Mark battery as calibrated if we see any reading above 0% (not stuck at 0%)
            if battery > 0 and not session.battery_calibrated:
                session.battery_calibrated = True
                _LOGGER.info("RAPT BATTERY: Battery calibrated at %d%% for session: %s",
                             battery, session.name)

            # Only warn about low battery if it's been calibrated (prevents 0% startup warnings)
            if (session.battery_calibrated and
                battery < self.low_battery_threshold):
                await self.async_add_alert(
                    session,
                    ALERT_TYPE_LOW_BATTERY,
                    f"Low battery: {battery}%"
                )

    async def async_add_alert(self, session: BrewingSession, alert_type: str, message: str) -> None:
        """Add an alert to the session, notifying and firing an event."""
        now = dt_util.now()

        if alert_type in ONCE_PER_SESSION_ALERTS:
            # Only alert once per session (not recurring)
            if any(alert.type == alert_type for alert in session.alerts):
                _LOGGER.debug("RAPT ALERT SKIPPED (once per session): Type=%s, Session=%s",
                              alert_type, session.name)
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

        # Fire an event so users can build automations on alerts
        self.hass.bus.async_fire(
            EVENT_RAPT_BREWING_ALERT,
            {
                "entry_id": self.entry.entry_id,
                "alert_type": alert_type,
                "message": message,
                "session_id": session.id,
                "session_name": session.name,
            },
        )

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

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    async def start_session(self, name: str, recipe: str | None = None,
                          original_gravity: float | None = None,
                          target_gravity: float | None = None,
                          target_temperature: float | None = None) -> str:
        """Start a new brewing session, stopping any currently active ones."""
        for existing in self.data.sessions.values():
            if existing.state == SESSION_STATE_ACTIVE:
                existing.state = SESSION_STATE_IDLE
                existing.completed_at = dt_util.now()
                _LOGGER.info("RAPT SESSION: Auto-stopped session: %s", existing.name)

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

        await self.async_save_data()
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

            await self.async_save_data()

    async def delete_session(self, session_id: str) -> None:
        """Delete a brewing session."""
        if self.data.current_session and self.data.current_session.id == session_id:
            self.data.set_current_session(None)

        self.data.remove_session(session_id)
        await self.async_save_data()

    async def select_session(self, session_id: str) -> None:
        """Switch the currently viewed session."""
        self.data.set_current_session(session_id)
        await self.async_save_data()
        await self.async_request_refresh()

    async def add_session_note(self, note: str) -> None:
        """Append a timestamped note to the current session."""
        session = self.data.current_session
        if not session:
            raise ValueError("No current brewing session to add a note to")

        line = f"[{dt_util.now().strftime('%Y-%m-%d %H:%M')}] {note.strip()}"
        session.notes = f"{session.notes}\n{line}" if session.notes else line
        await self.async_save_data()
        await self.async_request_refresh()

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------

    def _data_to_save(self) -> dict[str, Any]:
        """Build the storage payload."""
        return {
            "sessions": {
                session_id: session.to_dict()
                for session_id, session in self.data.sessions.items()
            },
            "current_session_id": self.data.current_session.id if self.data.current_session else None,
            "settings": self.data.settings,
        }

    def _schedule_save(self) -> None:
        """Schedule a delayed save to limit disk writes on periodic updates."""
        self.store.async_delay_save(self._data_to_save, SAVE_DELAY_SECONDS)

    async def async_save_data(self) -> None:
        """Save data to storage immediately."""
        await self.store.async_save(self._data_to_save())

    async def _load_data(self) -> None:
        """Load data from storage."""
        stored_data = await self.store.async_load()

        if stored_data is None:
            # Migrate from the legacy shared storage file (pre-2.7.0) which
            # was not scoped per config entry.
            legacy_store = Store(self.hass, STORAGE_VERSION, LEGACY_STORAGE_KEY)
            stored_data = await legacy_store.async_load()
            if stored_data is not None:
                _LOGGER.info("Migrating legacy session storage to per-entry storage for %s",
                             self.entry.entry_id)
                await self.store.async_save(stored_data)
                await legacy_store.async_remove()

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
        if self._entity_cancel_callback:
            self._entity_cancel_callback()
            self._entity_cancel_callback = None
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
