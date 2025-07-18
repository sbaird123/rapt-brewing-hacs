"""Number input entities for RAPT Brewing integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import RAPTBrewingEntity

if TYPE_CHECKING:
    from .coordinator import RAPTBrewingCoordinator

_LOGGER = logging.getLogger(__name__)

NUMBER_TYPES: tuple[NumberEntityDescription, ...] = (
    NumberEntityDescription(
        key="target_gravity",
        name="Target Gravity",
        icon="mdi:speedometer",
        native_min_value=0.990,
        native_max_value=1.200,
        native_step=0.001,
        native_unit_of_measurement="SG",
    ),
    NumberEntityDescription(
        key="original_gravity",
        name="Original Gravity",
        icon="mdi:speedometer-medium",
        native_min_value=1.000,
        native_max_value=1.200,
        native_step=0.001,
        native_unit_of_measurement="SG",
    ),
    NumberEntityDescription(
        key="target_temperature",
        name="Target Temperature",
        icon="mdi:thermometer",
        native_min_value=0.0,
        native_max_value=50.0,
        native_step=0.1,
        native_unit_of_measurement="°C",
    ),
    NumberEntityDescription(
        key="starting_pressure",
        name="Starting Pressure",
        icon="mdi:gauge",
        native_min_value=0.0,
        native_max_value=50.0,
        native_step=0.1,
        native_unit_of_measurement="PSI",
    ),
    NumberEntityDescription(
        key="current_pressure",
        name="Current Pressure",
        icon="mdi:gauge-full",
        native_min_value=0.0,
        native_max_value=50.0,
        native_step=0.1,
        native_unit_of_measurement="PSI",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RAPT Brewing number entities."""
    coordinator: RAPTBrewingCoordinator = entry.runtime_data
    
    entities = [
        RAPTBrewingNumber(coordinator, description)
        for description in NUMBER_TYPES
    ]
    
    async_add_entities(entities)


class RAPTBrewingNumber(RAPTBrewingEntity, NumberEntity):
    """Represent a RAPT Brewing number entity."""

    def __init__(
        self,
        coordinator: RAPTBrewingCoordinator,
        description: NumberEntityDescription,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{description.key}"
        self._attr_mode = "box"

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data.current_session:
            return None
            
        session = self.coordinator.data.current_session
        
        if self.entity_description.key == "target_gravity":
            return session.target_gravity
        elif self.entity_description.key == "original_gravity":
            return session.original_gravity
        elif self.entity_description.key == "target_temperature":
            return session.target_temperature
        elif self.entity_description.key == "starting_pressure":
            return session.starting_pressure
        elif self.entity_description.key == "current_pressure":
            return session.current_pressure
        
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set the number value."""
        if not self.coordinator.data.current_session:
            _LOGGER.warning("RAPT NUMBER: Cannot set %s, no current session", self.entity_description.key)
            return
            
        session = self.coordinator.data.current_session
        
        if self.entity_description.key == "target_gravity":
            session.target_gravity = value
            _LOGGER.warning("RAPT NUMBER: Set target gravity to %.3f for session: %s", value, session.name)
        elif self.entity_description.key == "original_gravity":
            session.original_gravity = value
            _LOGGER.warning("RAPT NUMBER: Set original gravity to %.3f for session: %s", value, session.name)
        elif self.entity_description.key == "target_temperature":
            session.target_temperature = value
            _LOGGER.warning("RAPT NUMBER: Set target temperature to %.1f°C for session: %s", value, session.name)
        elif self.entity_description.key == "starting_pressure":
            session.starting_pressure = value
            session.pressure_fermentation = value > 0  # Enable pressure fermentation if pressure is set
            _LOGGER.warning("RAPT NUMBER: Set starting pressure to %.1f PSI for session: %s", value, session.name)
        elif self.entity_description.key == "current_pressure":
            session.current_pressure = value
            _LOGGER.warning("RAPT NUMBER: Set current pressure to %.1f PSI for session: %s", value, session.name)
        
        await self.coordinator._save_data()
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data.current_session is not None