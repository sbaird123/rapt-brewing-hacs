"""Config flow for RAPT Brewing integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
try:
    from homeassistant.components.bluetooth import (
        BluetoothServiceInfoBleak,
        async_discovered_service_info,
    )
    BLUETOOTH_AVAILABLE = True
except ImportError:
    # Bluetooth component not available
    BLUETOOTH_AVAILABLE = False
    BluetoothServiceInfoBleak = None
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_RAPT_DEVICE_ID

# BLE constants - defined inline to avoid circular imports
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
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

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
        
        if not discovered_devices and user_input is None:
            # No devices found, but allow manual entry
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors={"base": "no_devices_found"},
                description_placeholders={
                    "devices_count": "0"
                }
            )
        
        if user_input is not None:
            # Check if this is a discovered device or manual entry
            rapt_device_id = user_input[CONF_RAPT_DEVICE_ID]
            
            if rapt_device_id in self._discovered_devices:
                # Use discovered device
                device_info = self._discovered_devices[rapt_device_id]
                title = f"RAPT Pill ({device_info.name or rapt_device_id[:8]})"
            else:
                # Manual entry
                title = f"RAPT Brewing - {rapt_device_id}"
            
            # Check for existing entries
            await self.async_set_unique_id(rapt_device_id)
            self._abort_if_unique_id_configured()
            
            # Create the config entry
            return self.async_create_entry(
                title=title,
                data=user_input,
            )

        # Create dynamic schema with discovered devices
        if discovered_devices:
            device_options = {
                address: f"{info.name or 'RAPT Pill'} ({address[:8]}...)"
                for address, info in discovered_devices.items()
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
        
        if not BLUETOOTH_AVAILABLE:
            _LOGGER.warning("Bluetooth component not available")
            return discovered_devices
        
        # Get all discovered Bluetooth service info
        service_infos = async_discovered_service_info(self.hass)
        
        for service_info in service_infos:
            if self._is_rapt_device(service_info):
                discovered_devices[service_info.address] = service_info
                self._discovered_devices[service_info.address] = service_info
        
        _LOGGER.debug("Discovered %d RAPT devices", len(discovered_devices))
        return discovered_devices
    
    def _is_rapt_device(self, service_info: Any) -> bool:
        """Check if a Bluetooth device is a RAPT Pill."""
        manufacturer_data = service_info.manufacturer_data
        
        # Check for RAPT manufacturer ID with correct data start
        if RAPT_MANUFACTURER_ID in manufacturer_data:
            data = manufacturer_data[RAPT_MANUFACTURER_ID]
            if len(data) >= 2 and list(data[:2]) == RAPT_DATA_START:
                return True
        
        # Check for KegLand manufacturer ID
        if KEGLAND_MANUFACTURER_ID in manufacturer_data:
            return True
        
        # Check device name patterns
        name = service_info.name or ""
        if "rapt" in name.lower() or "pill" in name.lower():
            return True
        
        return False

    async def _async_validate_rapt_device(self, device_id: str) -> bool:
        """Validate that the RAPT device exists."""
        # Since we now have integrated BLE support, always allow setup
        # Bluetooth device validation will happen at runtime
        return True

    async def async_step_import(self, import_info: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_info)