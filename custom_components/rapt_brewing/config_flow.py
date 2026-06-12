"""Config flow for RAPT Brewing integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_RAPT_DEVICE_ID,
    CONF_NOTIFICATION_SERVICE,
    CONF_SOURCE_TYPE,
    CONF_GRAVITY_ENTITY,
    CONF_TEMPERATURE_ENTITY,
    CONF_BATTERY_ENTITY,
    CONF_SIGNAL_ENTITY,
    SOURCE_TYPE_BLUETOOTH,
    SOURCE_TYPE_ENTITY,
)

# BLE constants for discovery
RAPT_MANUFACTURER_ID = 16722  # 0x4152 - "RA" from RAPT
KEGLAND_MANUFACTURER_ID = 17739  # 0x454B - "KE" from KEG
RAPT_DATA_START = [80, 84]  # "PT" - Pill Telemetry

_LOGGER = logging.getLogger(__name__)


SOURCE_TYPE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SOURCE_TYPE, default=SOURCE_TYPE_BLUETOOTH): vol.In(
            {
                SOURCE_TYPE_BLUETOOTH: "Direct Bluetooth",
                SOURCE_TYPE_ENTITY: "Home Assistant entities (e.g. Shelly BLE proxy)",
            }
        )
    }
)


_NUMERIC_DOMAINS = ["sensor", "input_number", "number"]


def _entity_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Schema for choosing HA entities as the data source.

    Accepts sensor, number, and input_number so that template sensors and
    helpers can be used alongside real proxy-provided sensors.
    """
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_GRAVITY_ENTITY,
                default=defaults.get(CONF_GRAVITY_ENTITY),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=_NUMERIC_DOMAINS)
            ),
            vol.Required(
                CONF_TEMPERATURE_ENTITY,
                default=defaults.get(CONF_TEMPERATURE_ENTITY),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=_NUMERIC_DOMAINS)
            ),
            vol.Required(
                CONF_BATTERY_ENTITY,
                default=defaults.get(CONF_BATTERY_ENTITY),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=_NUMERIC_DOMAINS)
            ),
            vol.Optional(
                CONF_SIGNAL_ENTITY,
                default=defaults.get(CONF_SIGNAL_ENTITY, vol.UNDEFINED),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=_NUMERIC_DOMAINS)
            ),
        }
    )


class RAPTBrewingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RAPT Brewing."""

    VERSION = 2

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return RAPTBrewingOptionsFlow()

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices: dict[str, Any] = {}
        self._discovery_info: Any = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ask the user which data source to use."""
        if user_input is not None:
            if user_input[CONF_SOURCE_TYPE] == SOURCE_TYPE_ENTITY:
                return await self.async_step_entity()
            return await self.async_step_bluetooth_select()

        return self.async_show_form(
            step_id="user",
            data_schema=SOURCE_TYPE_SCHEMA,
        )

    async def async_step_bluetooth(self, discovery_info: Any) -> FlowResult:
        """Handle a RAPT Pill discovered via Bluetooth (manifest matchers)."""
        address = discovery_info.address.upper()
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {"name": f"RAPT Pill ({address})"}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm adding a discovered RAPT Pill."""
        address = self._discovery_info.address.upper()
        if user_input is not None:
            return self.async_create_entry(
                title=f"RAPT Pill ({address[:8]}...)",
                data={
                    CONF_SOURCE_TYPE: SOURCE_TYPE_BLUETOOTH,
                    CONF_RAPT_DEVICE_ID: address,
                },
            )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"address": address},
        )

    async def async_step_bluetooth_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure a direct Bluetooth data source."""
        discovered_devices = await self._async_discover_rapt_devices()

        if user_input is not None:
            rapt_device_id = user_input[CONF_RAPT_DEVICE_ID]
            if rapt_device_id == "manual":
                return await self.async_step_bluetooth_manual()
            return await self._async_create_bluetooth_entry(rapt_device_id)

        if not discovered_devices:
            return await self.async_step_bluetooth_manual()

        device_options = {
            address: f"RAPT Pill ({address[:8]}...)"
            for address in discovered_devices.keys()
        }
        device_options["manual"] = "Enter manually"
        schema = vol.Schema(
            {vol.Required(CONF_RAPT_DEVICE_ID): vol.In(device_options)}
        )

        return self.async_show_form(
            step_id="bluetooth_select",
            data_schema=schema,
            description_placeholders={
                "devices_count": str(len(discovered_devices))
            },
        )

    async def async_step_bluetooth_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Enter a Bluetooth device address manually."""
        errors: dict[str, str] = {}

        if user_input is not None:
            rapt_device_id = user_input[CONF_RAPT_DEVICE_ID].strip().upper()
            if rapt_device_id and rapt_device_id != "MANUAL":
                return await self._async_create_bluetooth_entry(rapt_device_id)
            errors["base"] = "invalid_device"

        return self.async_show_form(
            step_id="bluetooth_manual",
            data_schema=vol.Schema({vol.Required(CONF_RAPT_DEVICE_ID): cv.string}),
            errors=errors,
        )

    async def _async_create_bluetooth_entry(self, rapt_device_id: str) -> FlowResult:
        """Create a config entry for a Bluetooth-sourced RAPT Pill."""
        rapt_device_id = rapt_device_id.strip().upper()

        await self.async_set_unique_id(rapt_device_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"RAPT Pill ({rapt_device_id[:8]}...)",
            data={
                CONF_SOURCE_TYPE: SOURCE_TYPE_BLUETOOTH,
                CONF_RAPT_DEVICE_ID: rapt_device_id,
            },
        )

    async def async_step_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure an entity-based data source."""
        if user_input is not None:
            unique_id = f"entity:{user_input[CONF_GRAVITY_ENTITY]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"RAPT Brewing ({user_input[CONF_GRAVITY_ENTITY]})",
                data={CONF_SOURCE_TYPE: SOURCE_TYPE_ENTITY, **user_input},
            )

        return self.async_show_form(
            step_id="entity",
            data_schema=_entity_schema(),
        )

    async def _async_discover_rapt_devices(self) -> dict[str, Any]:
        """Discover RAPT devices via Bluetooth."""
        discovered_devices = {}

        try:
            from homeassistant.components.bluetooth import async_discovered_service_info

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

            _LOGGER.debug("Checking device %s with manufacturer data: %s",
                         service_info.address, manufacturer_data)

            if RAPT_MANUFACTURER_ID in manufacturer_data:
                data = manufacturer_data[RAPT_MANUFACTURER_ID]
                if len(data) >= 2 and list(data[:2]) == RAPT_DATA_START:
                    return True

            if KEGLAND_MANUFACTURER_ID in manufacturer_data:
                return True

            name = getattr(service_info, 'name', '') or ""
            if name and ("rapt" in name.lower() or "pill" in name.lower()):
                return True

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
        return await self.async_step_bluetooth_select(import_info)


class RAPTBrewingOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for RAPT Brewing."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Choose what to configure."""
        menu = ["notifications"]
        if self.config_entry.data.get(CONF_SOURCE_TYPE) == SOURCE_TYPE_ENTITY:
            menu.append("entities")
        return self.async_show_menu(step_id="init", menu_options=menu)

    async def async_step_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage notification options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        notification_services = await self._get_notification_services()

        options_schema = vol.Schema({
            vol.Optional(
                CONF_NOTIFICATION_SERVICE,
                default=self.config_entry.options.get(CONF_NOTIFICATION_SERVICE, "")
            ): vol.In([""] + notification_services)
        })

        return self.async_show_form(
            step_id="notifications",
            data_schema=options_schema,
            description_placeholders={
                "notification_services": ", ".join(notification_services) if notification_services else "None found"
            }
        )

    async def async_step_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Reconfigure the source entities."""
        if user_input is not None:
            new_data = {**self.config_entry.data, **user_input}
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data
            )
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="entities",
            data_schema=_entity_schema(dict(self.config_entry.data)),
        )

    async def _get_notification_services(self) -> list[str]:
        """Get list of available notification services."""
        try:
            services = self.hass.services.async_services()
            notify_services = []

            if "notify" in services:
                for service_name in services["notify"]:
                    if service_name != "notify":
                        notify_services.append(f"notify.{service_name}")

            return sorted(notify_services)
        except Exception:
            return []
