"""Base entity for RAPT Brewing integration."""
from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

if TYPE_CHECKING:
    from .coordinator import RAPTBrewingCoordinator


class RAPTBrewingEntity(CoordinatorEntity):
    """Base class for RAPT Brewing entities."""

    def __init__(
        self,
        coordinator: RAPTBrewingCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._key = key
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry.entry_id}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title or "RAPT Brewing Session Manager",
            manufacturer="RAPT",
            model="Brewing Session Manager",
            sw_version="1.0.0",
        )
