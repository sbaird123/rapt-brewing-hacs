"""Base entity for RAPT Brewing integration."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

if TYPE_CHECKING:
    from .coordinator import RAPTBrewingCoordinator


class RAPTBrewingEntity(CoordinatorEntity):
    """Base class for RAPT Brewing entities."""

    def __init__(self, coordinator: RAPTBrewingCoordinator, key: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._key = key
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, "rapt_brewing")},
            name="RAPT Brewing Session Manager",
            manufacturer="RAPT",
            model="Brewing Session Manager",
            sw_version="1.0.0",
        )

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{DOMAIN}_{self._key}"