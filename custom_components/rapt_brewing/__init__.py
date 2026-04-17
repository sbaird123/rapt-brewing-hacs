"""RAPT Brewing Session Manager integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

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

    if entry.version < 2:
        # v1 → v2: entity unique IDs and device identifiers were not scoped to
        # the config entry, which prevented adding a second entry. Rewrite the
        # legacy prefix "rapt_brewing_<key>" to "<entry_id>_<key>" and the
        # legacy device identifier (DOMAIN, "rapt_brewing") to
        # (DOMAIN, entry_id) so history is preserved.
        ent_reg = er.async_get(hass)
        legacy_prefix = f"{DOMAIN}_"
        new_prefix = f"{entry.entry_id}_"

        for er_entry in list(ent_reg.entities.values()):
            if er_entry.config_entry_id != entry.entry_id:
                continue
            if er_entry.unique_id.startswith(legacy_prefix):
                new_unique_id = new_prefix + er_entry.unique_id[len(legacy_prefix):]
                _LOGGER.info(
                    "Migrating entity unique_id %s → %s",
                    er_entry.unique_id, new_unique_id,
                )
                ent_reg.async_update_entity(
                    er_entry.entity_id, new_unique_id=new_unique_id
                )

        dev_reg = dr.async_get(hass)
        legacy_device = dev_reg.async_get_device(
            identifiers={(DOMAIN, "rapt_brewing")}
        )
        if legacy_device and entry.entry_id in legacy_device.config_entries:
            _LOGGER.info(
                "Migrating device identifier (%s, rapt_brewing) → (%s, %s)",
                DOMAIN, DOMAIN, entry.entry_id,
            )
            dev_reg.async_update_device(
                legacy_device.id,
                new_identifiers={(DOMAIN, entry.entry_id)},
            )

        hass.config_entries.async_update_entry(entry, version=2)

    return True
