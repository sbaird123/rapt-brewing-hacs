"""Config flow for RAPT Brewing integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_RAPT_DEVICE_ID, CONF_NOTIFICATION_SERVICE

# BLE constants for discovery
RAPT_MANUFACTURER_ID = 16722  # 0x4152 - "RA" from RAPT
KEGLAND_MANUFACTURER_ID = 17739  # 0x454B - "KE" from KEG
RAPT_DATA_START = [80, 84]  # "PT" - Pill Telemetry

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_RAPT_DEVICE_ID): cv.string,
    }
)


class RAPTBrewingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RAPT Brewing."""

    VERSION = 1
    
    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return RAPTBrewingOptionsFlow(config_entry)

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        # Discover RAPT devices via Bluetooth
        discovered_devices = await self._async_discover_rapt_devices()
        
        if user_input is not None:
            rapt_device_id = user_input[CONF_RAPT_DEVICE_ID]
            
            # Check for existing entries
            await self.async_set_unique_id(rapt_device_id)
            self._abort_if_unique_id_configured()
            
            # Determine title based on discovered device or manual entry
            if rapt_device_id in self._discovered_devices:
                device_info = self._discovered_devices[rapt_device_id]
                title = f"RAPT Pill ({rapt_device_id[:8]}...)"
            else:
                title = f"RAPT Brewing - {rapt_device_id}"
            
            # Create the config entry
            return self.async_create_entry(
                title=title,
                data=user_input,
            )

        # Create dynamic schema with discovered devices
        if discovered_devices:
            device_options = {
                address: f"RAPT Pill ({address[:8]}...)"
                for address in discovered_devices.keys()
            }
            device_options["manual"] = "Enter manually"
            
            schema = vol.Schema({
                vol.Required(CONF_RAPT_DEVICE_ID): vol.In(device_options)
            })
        else:
            schema = STEP_USER_DATA_SCHEMA

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "devices_count": str(len(discovered_devices))
            }
        )

    async def _async_discover_rapt_devices(self) -> dict[str, Any]:
        """Discover RAPT devices via Bluetooth."""
        discovered_devices = {}
        
        try:
            # Import Bluetooth functions at runtime to avoid blocking imports
            from homeassistant.components.bluetooth import async_discovered_service_info
            
            # Get all discovered Bluetooth service info
            service_infos = async_discovered_service_info(self.hass)
            
            for service_info in service_infos:
                if self._is_rapt_device(service_info):
                    discovered_devices[service_info.address] = service_info
                    self._discovered_devices[service_info.address] = service_info
            
            _LOGGER.debug("Discovered %d RAPT devices: %s", len(discovered_devices), list(discovered_devices.keys()))
            
        except Exception as e:
            _LOGGER.warning("Could not discover Bluetooth devices: %s", e)
        
        return discovered_devices
    
    def _is_rapt_device(self, service_info: Any) -> bool:
        """Check if a Bluetooth device is a RAPT Pill."""
        try:
            manufacturer_data = service_info.manufacturer_data
            
            # Debug: Log what we're checking
            _LOGGER.debug("Checking device %s with manufacturer data: %s", 
                         service_info.address, manufacturer_data)
            
            
            # Check for RAPT manufacturer ID with correct data start  
            if RAPT_MANUFACTURER_ID in manufacturer_data:
                data = manufacturer_data[RAPT_MANUFACTURER_ID]
                if len(data) >= 2 and list(data[:2]) == RAPT_DATA_START:
                    return True
            
            # Check for KegLand manufacturer ID
            if KEGLAND_MANUFACTURER_ID in manufacturer_data:
                return True
            
            # Check device name patterns
            name = getattr(service_info, 'name', '') or ""
            if name and ("rapt" in name.lower() or "pill" in name.lower()):
                return True
            
            # Check service UUIDs
            service_uuids = getattr(service_info, 'service_uuids', []) or []
            rapt_service = "0000fe61-0000-1000-8000-00805f9b34fb"
            if rapt_service in service_uuids:
                _LOGGER.debug("Found RAPT service UUID!")
                return True
                
        except Exception as e:
            _LOGGER.debug("Error checking device %s: %s", getattr(service_info, 'address', 'unknown'), e)
        
        return False

    async def async_step_import(self, import_info: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_info)


class RAPTBrewingOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for RAPT Brewing."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get all available notification services
        notification_services = await self._get_notification_services()
        
        # Create options schema
        options_schema = vol.Schema({
            vol.Optional(
                CONF_NOTIFICATION_SERVICE,
                default=self.config_entry.options.get(CONF_NOTIFICATION_SERVICE, "")
            ): vol.In([""] + notification_services)
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            description_placeholders={
                "notification_services": ", ".join(notification_services) if notification_services else "None found"
            }
        )

    async def _get_notification_services(self) -> list[str]:
        """Get list of available notification services."""
        try:
            # Get all notification services from Home Assistant
            services = self.hass.services.async_services()
            notify_services = []
            
            if "notify" in services:
                for service_name in services["notify"]:
                    if service_name != "notify":  # Skip the generic notify service
                        notify_services.append(f"notify.{service_name}")
            
            return sorted(notify_services)
        except Exception:
            return []