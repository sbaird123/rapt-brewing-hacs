"""Sensor entities for RAPT Brewing integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import RAPTBrewingEntity

if TYPE_CHECKING:
    from .coordinator import RAPTBrewingCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="session_name",
        name="Session Name",
        icon="mdi:beer",
    ),
    SensorEntityDescription(
        key="original_gravity",
        name="Original Gravity",
        icon="mdi:speedometer",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="current_gravity",
        name="Current Gravity",
        icon="mdi:speedometer",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="current_gravity_temp_corrected",
        name="Current Gravity (Temp Corrected)",
        icon="mdi:speedometer-slow",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="target_gravity",
        name="Target Gravity",
        icon="mdi:target",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="alcohol_percentage",
        name="Alcohol Percentage",
        icon="mdi:glass-mug-variant",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="attenuation",
        name="Attenuation",
        icon="mdi:chart-line",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="fermentation_rate",
        name="Fermentation Rate",
        icon="mdi:trending-down",
        native_unit_of_measurement="SG/hr",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="current_temperature",
        name="Current Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="target_temperature",
        name="Target Temperature",
        icon="mdi:thermometer-lines",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="battery_level",
        name="RAPT Pill Battery",
        icon="mdi:battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="signal_strength",
        name="RAPT Pill Signal",
        icon="mdi:signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement="dBm",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="session_duration",
        name="Session Duration",
        icon="mdi:clock-outline",
        native_unit_of_measurement="hours",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="active_alerts",
        name="Active Alerts",
        icon="mdi:alert",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="last_reading_time",
        name="Last Reading Time",
        icon="mdi:clock",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    # New sensors from comprehensive BLE parsing
    SensorEntityDescription(
        key="gravity_velocity",
        name="Gravity Velocity",
        icon="mdi:speedometer",
        native_unit_of_measurement="SG/day",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="accelerometer_x",
        name="Accelerometer X",
        icon="mdi:axis-x-arrow",
        native_unit_of_measurement="g",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="accelerometer_y",
        name="Accelerometer Y",
        icon="mdi:axis-y-arrow",
        native_unit_of_measurement="g",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="accelerometer_z",
        name="Accelerometer Z",
        icon="mdi:axis-z-arrow",
        native_unit_of_measurement="g",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="device_stability",
        name="Device Stability",
        icon="mdi:stability",
    ),
    SensorEntityDescription(
        key="fermentation_activity",
        name="Fermentation Activity",
        icon="mdi:bottle-wine",
    ),
    SensorEntityDescription(
        key="firmware_version",
        name="Firmware Version",
        icon="mdi:chip",
    ),
    SensorEntityDescription(
        key="device_type",
        name="Device Type",
        icon="mdi:devices",
    ),
    SensorEntityDescription(
        key="data_format_version",
        name="Data Format Version",
        icon="mdi:file-code",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RAPT Brewing sensor entities."""
    coordinator: RAPTBrewingCoordinator = entry.runtime_data
    
    entities = [
        RAPTBrewingSensor(coordinator, description)
        for description in SENSOR_TYPES
    ]
    
    async_add_entities(entities)


class RAPTBrewingSensor(RAPTBrewingEntity, SensorEntity):
    """Represent a RAPT Brewing sensor."""

    def __init__(
        self,
        coordinator: RAPTBrewingCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{description.key}"

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.entity_description.key == "session_name":
            return (
                self.coordinator.data.current_session.name
                if self.coordinator.data.current_session
                else None
            )
        elif self.entity_description.key == "original_gravity":
            return (
                self.coordinator.data.current_session.original_gravity
                if self.coordinator.data.current_session
                else None
            )
        elif self.entity_description.key == "current_gravity":
            return (
                self.coordinator.data.current_session.current_gravity
                if self.coordinator.data.current_session
                else None
            )
        elif self.entity_description.key == "current_gravity_temp_corrected":
            return (
                self._calculate_temperature_corrected_gravity()
                if self.coordinator.data.current_session
                else None
            )
        elif self.entity_description.key == "target_gravity":
            return (
                self.coordinator.data.current_session.target_gravity
                if self.coordinator.data.current_session
                else None
            )
        elif self.entity_description.key == "alcohol_percentage":
            return (
                round(self.coordinator.data.current_session.alcohol_percentage, 2)
                if self.coordinator.data.current_session and self.coordinator.data.current_session.alcohol_percentage
                else None
            )
        elif self.entity_description.key == "attenuation":
            return (
                round(self.coordinator.data.current_session.attenuation, 1)
                if self.coordinator.data.current_session and self.coordinator.data.current_session.attenuation
                else None
            )
        elif self.entity_description.key == "fermentation_rate":
            return (
                round(self.coordinator.data.current_session.fermentation_rate, 6)
                if self.coordinator.data.current_session and self.coordinator.data.current_session.fermentation_rate
                else None
            )
        elif self.entity_description.key == "current_temperature":
            return (
                self.coordinator.data.current_session.current_temperature
                if self.coordinator.data.current_session
                else None
            )
        elif self.entity_description.key == "target_temperature":
            return (
                self.coordinator.data.current_session.target_temperature
                if self.coordinator.data.current_session
                else None
            )
        elif self.entity_description.key == "battery_level":
            if self.coordinator.data.current_session and self.coordinator.data.current_session.data_points:
                latest_point = self.coordinator.data.current_session.data_points[-1]
                return latest_point.battery_level
            return None
        elif self.entity_description.key == "signal_strength":
            if self.coordinator.data.current_session and self.coordinator.data.current_session.data_points:
                latest_point = self.coordinator.data.current_session.data_points[-1]
                return latest_point.signal_strength
            return None
        elif self.entity_description.key == "session_duration":
            if self.coordinator.data.current_session and self.coordinator.data.current_session.started_at:
                import homeassistant.util.dt as dt_util
                if self.coordinator.data.current_session.completed_at:
                    duration = self.coordinator.data.current_session.completed_at - self.coordinator.data.current_session.started_at
                else:
                    duration = dt_util.now() - self.coordinator.data.current_session.started_at
                return round(duration.total_seconds() / 3600, 1)
            return None
        elif self.entity_description.key == "active_alerts":
            if self.coordinator.data.current_session:
                return len([
                    alert for alert in self.coordinator.data.current_session.alerts
                    if not alert.acknowledged
                ])
            return 0
        elif self.entity_description.key == "last_reading_time":
            if self.coordinator.data.current_session and self.coordinator.data.current_session.data_points:
                latest_point = self.coordinator.data.current_session.data_points[-1]
                return latest_point.timestamp
            return None
        # New sensors from comprehensive BLE parsing
        elif self.entity_description.key == "gravity_velocity":
            if self.coordinator.data.current_session and self.coordinator.data.current_session.data_points:
                latest_point = self.coordinator.data.current_session.data_points[-1]
                return getattr(latest_point, 'gravity_velocity', None)
            return None
        elif self.entity_description.key == "accelerometer_x":
            if self.coordinator.data.current_session and self.coordinator.data.current_session.data_points:
                latest_point = self.coordinator.data.current_session.data_points[-1]
                return getattr(latest_point, 'accelerometer_x', None)
            return None
        elif self.entity_description.key == "accelerometer_y":
            if self.coordinator.data.current_session and self.coordinator.data.current_session.data_points:
                latest_point = self.coordinator.data.current_session.data_points[-1]
                return getattr(latest_point, 'accelerometer_y', None)
            return None
        elif self.entity_description.key == "accelerometer_z":
            if self.coordinator.data.current_session and self.coordinator.data.current_session.data_points:
                latest_point = self.coordinator.data.current_session.data_points[-1]
                return getattr(latest_point, 'accelerometer_z', None)
            return None
        elif self.entity_description.key == "device_stability":
            return self._calculate_device_stability()
        elif self.entity_description.key == "fermentation_activity":
            return self._calculate_fermentation_activity()
        elif self.entity_description.key == "firmware_version":
            if self.coordinator.data.current_session and self.coordinator.data.current_session.data_points:
                latest_point = self.coordinator.data.current_session.data_points[-1]
                return getattr(latest_point, 'firmware_version', None)
            return None
        elif self.entity_description.key == "device_type":
            if self.coordinator.data.current_session and self.coordinator.data.current_session.data_points:
                latest_point = self.coordinator.data.current_session.data_points[-1]
                return getattr(latest_point, 'device_type', None)
            return None
        elif self.entity_description.key == "data_format_version":
            if self.coordinator.data.current_session and self.coordinator.data.current_session.data_points:
                latest_point = self.coordinator.data.current_session.data_points[-1]
                return getattr(latest_point, 'data_format_version', None)
            return None
        
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        attrs = {}
        
        if self.coordinator.data.current_session:
            session = self.coordinator.data.current_session
            
            if self.entity_description.key == "session_name":
                attrs.update({
                    "recipe": session.recipe,
                    "started_at": session.started_at.isoformat() if session.started_at else None,
                    "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                    "notes": session.notes,
                })
            elif self.entity_description.key == "current_gravity":
                attrs.update({
                    "gravity_points": len([dp for dp in session.data_points if dp.gravity is not None]),
                    "last_24h_points": len([
                        dp for dp in session.data_points[-24:]
                        if dp.gravity is not None
                    ]),
                })
            elif self.entity_description.key == "fermentation_rate":
                if session.fermentation_rate is not None:
                    attrs.update({
                        "trend": "decreasing" if session.fermentation_rate < -0.001 else "stable" if abs(session.fermentation_rate) <= 0.001 else "increasing",
                        "rate_per_day": round(session.fermentation_rate * 24, 4) if session.fermentation_rate else None,
                    })
            elif self.entity_description.key == "active_alerts":
                attrs.update({
                    "alerts": [
                        {
                            "type": alert.type,
                            "message": alert.message,
                            "timestamp": alert.timestamp.isoformat(),
                            "acknowledged": alert.acknowledged,
                        }
                        for alert in session.alerts
                        if not alert.acknowledged
                    ]
                })
        
        return attrs
    
    def _calculate_temperature_corrected_gravity(self) -> float | None:
        """Calculate temperature-corrected specific gravity.
        
        Uses the coordinator's improved temperature correction that reduces
        sensitivity during stalled fermentation to prevent temperature-driven
        gravity fluctuations when fermentation is complete.
        """
        if not self.coordinator.data.current_session:
            return None
        
        # Use coordinator's temperature correction method for consistency
        temp_corrected = self.coordinator._get_temperature_corrected_gravity(
            self.coordinator.data.current_session
        )
        
        return round(temp_corrected, 4) if temp_corrected is not None else None
    
    def _calculate_device_stability(self) -> str | None:
        """Calculate device stability based on accelerometer data."""
        if not self.coordinator.data.current_session or not self.coordinator.data.current_session.data_points:
            return None
            
        # Get recent data points (last 5 readings)
        recent_points = self.coordinator.data.current_session.data_points[-5:]
        
        # Check if we have accelerometer data
        accel_points = [
            point for point in recent_points 
            if hasattr(point, 'accelerometer_x') and 
               hasattr(point, 'accelerometer_y') and 
               hasattr(point, 'accelerometer_z') and
               point.accelerometer_x is not None and
               point.accelerometer_y is not None and
               point.accelerometer_z is not None
        ]
        
        if len(accel_points) < 2:
            return "Unknown"
        
        # Calculate standard deviation of accelerometer readings
        import statistics
        
        x_values = [point.accelerometer_x for point in accel_points]
        y_values = [point.accelerometer_y for point in accel_points]
        z_values = [point.accelerometer_z for point in accel_points]
        
        try:
            x_std = statistics.stdev(x_values) if len(x_values) > 1 else 0
            y_std = statistics.stdev(y_values) if len(y_values) > 1 else 0
            z_std = statistics.stdev(z_values) if len(z_values) > 1 else 0
            
            # Calculate overall stability metric
            stability_metric = (x_std + y_std + z_std) / 3
            
            # Classify stability
            if stability_metric < 0.05:
                return "Very Stable"
            elif stability_metric < 0.15:
                return "Stable"
            elif stability_metric < 0.35:
                return "Slightly Unstable"
            else:
                return "Unstable"
                
        except Exception:
            return "Unknown"
    
    def _calculate_fermentation_activity(self) -> str | None:
        """Calculate fermentation activity based on averaged gravity velocity and accelerometer data over the last hour."""
        if not self.coordinator.data.current_session or not self.coordinator.data.current_session.data_points:
            return None
        
        from datetime import timedelta
        import homeassistant.util.dt as dt_util
        
        # Get points from the last hour for averaging
        now = dt_util.now()
        one_hour_ago = now - timedelta(hours=1)
        
        recent_points = [
            point for point in self.coordinator.data.current_session.data_points
            if point.timestamp >= one_hour_ago
        ]
        
        if len(recent_points) < 2:
            return "Unknown"
        
        # Average gravity velocity from RAPT over the last hour
        gravity_velocities = []
        for point in recent_points:
            velocity = getattr(point, 'gravity_velocity', None)
            if velocity is not None:
                gravity_velocities.append(abs(velocity))
        
        # Calculate average fermentation rate over the last hour as backup
        avg_fermentation_rate = None
        if len(recent_points) >= 2:
            time_span = (recent_points[-1].timestamp - recent_points[0].timestamp).total_seconds() / 3600  # hours
            if time_span > 0:
                gravities = [point.gravity for point in recent_points if point.gravity is not None]
                if len(gravities) >= 2:
                    gravity_change = abs(gravities[-1] - gravities[0])
                    avg_fermentation_rate = gravity_change / time_span  # SG/hour over the last hour
        
        # Get accelerometer variation (CO2 bubbles cause vibration) - averaged over last hour
        accel_variation = self._get_accelerometer_variation(recent_points)
        
        # Classify fermentation activity using averaged values
        if gravity_velocities:
            # Use averaged official gravity velocity from RAPT (points per day)
            # Convert to scientifically accurate thresholds
            avg_velocity = sum(gravity_velocities) / len(gravity_velocities)
            
            if avg_velocity > 19.0:  # >19 points/day - peak fermentation
                if accel_variation and accel_variation > 0.2:
                    return "Vigorous"
                else:
                    return "Active"
            elif avg_velocity > 10.0:  # >10 points/day - good fermentation
                return "Active"
            elif avg_velocity > 2.0:  # >2 points/day - steady progress
                return "Moderate"
            elif avg_velocity > 1.0:  # >1 point/day - slow but progressing
                return "Slow"
            else:  # ≤1 point/day - effectively stalled
                return "Inactive"
        
        elif avg_fermentation_rate is not None:
            # Use scientifically accurate fermentation rate thresholds based on real brewing data
            from .const import (
                FERMENTATION_RATE_VIGOROUS, 
                FERMENTATION_RATE_ACTIVE,
                FERMENTATION_RATE_MODERATE, 
                FERMENTATION_RATE_SLOW,
                FERMENTATION_RATE_STUCK
            )
            
            rate_abs = abs(avg_fermentation_rate)
            
            if rate_abs > FERMENTATION_RATE_VIGOROUS:  # >19 points/day
                if accel_variation and accel_variation > 0.2:
                    return "Vigorous"
                else:
                    return "Active"
            elif rate_abs > FERMENTATION_RATE_ACTIVE:  # >10 points/day
                return "Active"
            elif rate_abs > FERMENTATION_RATE_MODERATE:  # >2 points/day
                return "Moderate"
            elif rate_abs > FERMENTATION_RATE_SLOW:  # >1 point/day
                return "Slow"
            else:  # ≤1 point/day - effectively stalled
                return "Inactive"
        
        return "Unknown"
    
    def _get_accelerometer_variation(self, points: list) -> float | None:
        """Calculate accelerometer variation as an indicator of CO2 activity."""
        accel_points = [
            point for point in points 
            if hasattr(point, 'accelerometer_x') and 
               hasattr(point, 'accelerometer_y') and 
               hasattr(point, 'accelerometer_z') and
               point.accelerometer_x is not None and
               point.accelerometer_y is not None and
               point.accelerometer_z is not None
        ]
        
        if len(accel_points) < 3:
            return None
        
        try:
            import statistics
            
            # Calculate magnitude of each accelerometer reading
            magnitudes = [
                (point.accelerometer_x**2 + point.accelerometer_y**2 + point.accelerometer_z**2)**0.5
                for point in accel_points
            ]
            
            # Return standard deviation of magnitudes
            return statistics.stdev(magnitudes) if len(magnitudes) > 1 else 0
            
        except Exception:
            return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Some sensors are always available
        if self.entity_description.key in ("total_sessions", "session_state"):
            return True
        
        # Most sensors require an active session
        return self.coordinator.data.current_session is not None