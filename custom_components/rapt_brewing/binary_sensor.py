"""Binary sensor entities for RAPT Brewing integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import RAPTBrewingEntity

if TYPE_CHECKING:
    from .coordinator import RAPTBrewingCoordinator

_LOGGER = logging.getLogger(__name__)

BINARY_SENSOR_TYPES: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="device_online",
        name="Device Online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RAPT Brewing binary sensor entities."""
    coordinator: RAPTBrewingCoordinator = entry.runtime_data

    entities = [
        RAPTBrewingBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSOR_TYPES
    ]

    async_add_entities(entities)


class RAPTBrewingBinarySensor(RAPTBrewingEntity, BinarySensorEntity):
    """Represent a RAPT Brewing binary sensor."""

    def __init__(
        self,
        coordinator: RAPTBrewingCoordinator,
        entry: ConfigEntry,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        """Return True when fresh data has arrived within the offline timeout."""
        return self.coordinator.is_online

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        last = self.coordinator.last_data_received
        return {
            "source_type": self.coordinator.source_type,
            "last_data_received": last.isoformat() if last else None,
            "offline_timeout_minutes": self.coordinator.offline_timeout.total_seconds() / 60,
        }

    @property
    def available(self) -> bool:
        """The connectivity sensor itself is always available."""
        return True
