"""RAPT Brewing Session Manager integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

if TYPE_CHECKING:
    from .coordinator import RAPTBrewingCoordinator
    from .data import RAPTBrewingData

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON, Platform.TEXT, Platform.NUMBER]

_LOGGER = logging.getLogger(__name__)

# Type alias for config entry - remove generic typing to avoid issues
# RAPTBrewingConfigEntry = ConfigEntry[RAPTBrewingData]
RAPTBrewingConfigEntry = ConfigEntry


async def async_setup_entry(hass: HomeAssistant, entry: RAPTBrewingConfigEntry) -> bool:
    """Set up RAPT Brewing from a config entry."""
    try:
        # Import coordinator here to avoid blocking imports
        from .coordinator import RAPTBrewingCoordinator
        
        coordinator = RAPTBrewingCoordinator(hass, entry)
        
        # Do the first refresh (BLE coordinator will start automatically)
        await coordinator.async_config_entry_first_refresh()
        
        entry.runtime_data = coordinator
        
        # Forward setup to all platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        return True
    except Exception as e:
        _LOGGER.error("Failed to setup RAPT Brewing: %s", e)
        return False


async def async_unload_entry(hass: HomeAssistant, entry: RAPTBrewingConfigEntry) -> bool:
    """Unload a config entry."""
    # BLE coordinator will stop automatically when platforms are unloaded
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", entry.version)
    
    if entry.version == 1:
        # Migration logic here if needed
        pass
    
    return True