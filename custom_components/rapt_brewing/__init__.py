"""RAPT Brewing Session Manager integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_get

from .const import DOMAIN
from .coordinator import RAPTBrewingCoordinator

if TYPE_CHECKING:
    from .data import RAPTBrewingData

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON, Platform.SELECT]

_LOGGER = logging.getLogger(__name__)

# Type alias for config entry - remove generic typing to avoid issues
# RAPTBrewingConfigEntry = ConfigEntry[RAPTBrewingData]
RAPTBrewingConfigEntry = ConfigEntry


async def async_setup_entry(hass: HomeAssistant, entry: RAPTBrewingConfigEntry) -> bool:
    """Set up RAPT Brewing from a config entry."""
    try:
        coordinator = RAPTBrewingCoordinator(hass, entry)
        
        # Start the BLE coordinator first
        await coordinator.ble_coordinator.async_start()
        
        # Then do the first refresh
        await coordinator.async_config_entry_first_refresh()
        
        entry.runtime_data = coordinator
        
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        return True
    except Exception as e:
        _LOGGER.error("Failed to setup RAPT Brewing: %s", e)
        return False


async def async_unload_entry(hass: HomeAssistant, entry: RAPTBrewingConfigEntry) -> bool:
    """Unload a config entry."""
    # Stop the BLE coordinator
    coordinator = entry.runtime_data
    await coordinator.ble_coordinator.async_stop()
    
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", entry.version)
    
    if entry.version == 1:
        # Migration logic here if needed
        pass
    
    return True