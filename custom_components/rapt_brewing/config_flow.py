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
            rapt_device_id = user_input[CONF_RAPT_DEVICE_ID]
            
            # Check for existing entries
            await self.async_set_unique_id(rapt_device_id)
            self._abort_if_unique_id_configured()
            
            # Create the config entry
            return self.async_create_entry(
                title=f"RAPT Brewing - {rapt_device_id}",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "devices_count": "0"
            }
        )

    async def async_step_import(self, import_info: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_info)