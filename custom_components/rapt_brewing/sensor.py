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
        key="session_state",
        name="Session State",
        icon="mdi:state-machine",
    ),
    SensorEntityDescription(
        key="fermentation_stage",
        name="Fermentation Stage",
        icon="mdi:flask",
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
        key="total_sessions",
        name="Total Sessions",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL,
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
        elif self.entity_description.key == "session_state":
            return (
                self.coordinator.data.current_session.state
                if self.coordinator.data.current_session
                else "idle"
            )
        elif self.entity_description.key == "fermentation_stage":
            return (
                self.coordinator.data.current_session.stage
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
        elif self.entity_description.key == "total_sessions":
            return len(self.coordinator.data.sessions)
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
        
        return attrs if attrs else None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Some sensors are always available
        if self.entity_description.key in ("total_sessions", "session_state"):
            return True
        
        # Most sensors require an active session
        return self.coordinator.data.current_session is not None