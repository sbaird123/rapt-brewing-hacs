"""Config flow for RAPT Brewing integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_RAPT_DEVICE_ID

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_RAPT_DEVICE_ID): cv.string,
    }
)


class RAPTBrewingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RAPT Brewing."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            # Validate that the RAPT device exists
            rapt_device_id = user_input[CONF_RAPT_DEVICE_ID]
            
            if await self._async_validate_rapt_device(rapt_device_id):
                # Create the config entry
                return self.async_create_entry(
                    title=f"RAPT Brewing - {rapt_device_id}",
                    data=user_input,
                )
            else:
                errors["base"] = "invalid_device"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _async_validate_rapt_device(self, device_id: str) -> bool:
        """Validate that the RAPT device exists."""
        try:
            # Check if RAPT BLE integration is loaded
            if "rapt_ble" not in self.hass.data.get("integrations", {}):
                return False
            
            # Check if the device exists in entity registry
            entity_registry = self.hass.helpers.entity_registry.async_get(self.hass)
            
            # Look for RAPT BLE entities with this device ID
            for entity_id, entry in entity_registry.entities.items():
                if (entry.platform == "rapt_ble" and 
                    device_id in entity_id):
                    return True
                    
            return False
            
        except Exception:
            _LOGGER.exception("Error validating RAPT device")
            return False

    async def async_step_import(self, import_info: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_info)