"""Config flow for RAPT Brewing integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import aiohttp_client
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
    CONF_API_EMAIL,
    CONF_API_SECRET,
    CONF_HYDROMETER_ID,
    CONF_STUCK_FERMENTATION_HOURS,
    CONF_TEMPERATURE_HIGH_THRESHOLD,
    CONF_TEMPERATURE_LOW_THRESHOLD,
    CONF_LOW_BATTERY_THRESHOLD,
    CONF_OFFLINE_TIMEOUT_MINUTES,
    CONF_GRAVITY_OFFSET,
    CONF_TEMPERATURE_OFFSET,
    CONF_GRAVITY_UNIT,
    CONF_HEATER_SWITCH,
    CONF_COOLER_SWITCH,
    CONF_HEAT_PROPORTIONAL_BAND,
    CONF_HEAT_CYCLE_MINUTES,
    CONF_HEAT_INTEGRAL_HOURS,
    CONF_COOL_DEADBAND,
    CONF_COOL_MIN_ON_MINUTES,
    CONF_COOL_MIN_OFF_MINUTES,
    CONF_CHANGEOVER_MINUTES,
    CONF_MAX_HEAT_OVERSHOOT,
    CONF_ABSOLUTE_MAX_TEMPERATURE,
    GRAVITY_UNIT_SG,
    GRAVITY_UNIT_PLATO,
    SOURCE_TYPE_BLUETOOTH,
    SOURCE_TYPE_ENTITY,
    SOURCE_TYPE_CLOUD,
    DEFAULT_STUCK_FERMENTATION_HOURS,
    DEFAULT_TEMPERATURE_HIGH_THRESHOLD,
    DEFAULT_TEMPERATURE_LOW_THRESHOLD,
    DEFAULT_LOW_BATTERY_THRESHOLD,
    DEFAULT_OFFLINE_TIMEOUT_MINUTES,
    DEFAULT_OFFLINE_TIMEOUT_MINUTES_CLOUD,
    DEFAULT_HEAT_PROPORTIONAL_BAND,
    DEFAULT_HEAT_CYCLE_MINUTES,
    DEFAULT_HEAT_INTEGRAL_HOURS,
    DEFAULT_COOL_DEADBAND,
    DEFAULT_COOL_MIN_ON_MINUTES,
    DEFAULT_COOL_MIN_OFF_MINUTES,
    DEFAULT_CHANGEOVER_MINUTES,
    DEFAULT_MAX_HEAT_OVERSHOOT,
    DEFAULT_ABSOLUTE_MAX_TEMPERATURE,
)

# Domains that can act as a heater or cooler output
_OUTPUT_DOMAINS = ["switch", "input_boolean"]

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
                SOURCE_TYPE_CLOUD: "RAPT cloud (api.rapt.io)",
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


def _cloud_credentials_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Schema for RAPT cloud credentials."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_API_EMAIL, default=defaults.get(CONF_API_EMAIL, vol.UNDEFINED)
            ): cv.string,
            vol.Required(
                CONF_API_SECRET, default=defaults.get(CONF_API_SECRET, vol.UNDEFINED)
            ): cv.string,
        }
    )


async def _async_validate_cloud_credentials(
    hass, email: str, api_secret: str
) -> tuple[dict[str, str] | None, list[dict[str, Any]]]:
    """Validate cloud credentials. Returns (error, hydrometers)."""
    from .api import RAPTCloudAuthError, RAPTCloudClient, RAPTCloudError

    client = RAPTCloudClient(
        aiohttp_client.async_get_clientsession(hass), email, api_secret
    )
    try:
        hydrometers = await client.async_get_hydrometers()
    except RAPTCloudAuthError:
        return {"base": "invalid_auth"}, []
    except RAPTCloudError as err:
        _LOGGER.warning("RAPT cloud validation failed: %s", err)
        return {"base": "cannot_connect"}, []
    return None, hydrometers


def _hydrometer_id(hydrometer: dict[str, Any]) -> str | None:
    """Extract the ID from a hydrometer record."""
    raw = hydrometer.get("id", hydrometer.get("Id"))
    return str(raw) if raw is not None else None


def _hydrometer_name(hydrometer: dict[str, Any]) -> str:
    """Extract a display name from a hydrometer record."""
    return str(hydrometer.get("name", hydrometer.get("Name")) or "RAPT Pill")


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
        self._cloud_credentials: dict[str, str] = {}
        self._cloud_hydrometers: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ask the user which data source to use."""
        if user_input is not None:
            if user_input[CONF_SOURCE_TYPE] == SOURCE_TYPE_ENTITY:
                return await self.async_step_entity()
            if user_input[CONF_SOURCE_TYPE] == SOURCE_TYPE_CLOUD:
                return await self.async_step_cloud()
            return await self.async_step_bluetooth_select()

        return self.async_show_form(
            step_id="user",
            data_schema=SOURCE_TYPE_SCHEMA,
        )

    # ------------------------------------------------------------------
    # Bluetooth source
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Entity source
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Cloud source
    # ------------------------------------------------------------------

    async def async_step_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure a RAPT cloud data source: credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_API_EMAIL].strip()
            api_secret = user_input[CONF_API_SECRET].strip()
            error, hydrometers = await _async_validate_cloud_credentials(
                self.hass, email, api_secret
            )
            if error:
                errors = error
            elif not hydrometers:
                errors["base"] = "no_hydrometers"
            else:
                self._cloud_credentials = {
                    CONF_API_EMAIL: email,
                    CONF_API_SECRET: api_secret,
                }
                self._cloud_hydrometers = hydrometers
                return await self.async_step_cloud_device()

        return self.async_show_form(
            step_id="cloud",
            data_schema=_cloud_credentials_schema(),
            errors=errors,
        )

    async def async_step_cloud_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure a RAPT cloud data source: pick the hydrometer."""
        options = {
            hid: _hydrometer_name(h)
            for h in self._cloud_hydrometers
            if (hid := _hydrometer_id(h)) is not None
        }

        if user_input is not None:
            hydrometer_id = user_input[CONF_HYDROMETER_ID]
            await self.async_set_unique_id(f"cloud:{hydrometer_id}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"RAPT Pill ({options.get(hydrometer_id, hydrometer_id)})",
                data={
                    CONF_SOURCE_TYPE: SOURCE_TYPE_CLOUD,
                    CONF_HYDROMETER_ID: hydrometer_id,
                    **self._cloud_credentials,
                },
            )

        return self.async_show_form(
            step_id="cloud_device",
            data_schema=vol.Schema(
                {vol.Required(CONF_HYDROMETER_ID): vol.In(options)}
            ),
            description_placeholders={"devices_count": str(len(options))},
        )

    # ------------------------------------------------------------------
    # Reconfigure
    # ------------------------------------------------------------------

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Dispatch reconfiguration based on the entry's source type."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        source_type = entry.data.get(CONF_SOURCE_TYPE, SOURCE_TYPE_BLUETOOTH)
        if source_type == SOURCE_TYPE_ENTITY:
            return await self.async_step_reconfigure_entity()
        if source_type == SOURCE_TYPE_CLOUD:
            return await self.async_step_reconfigure_cloud()
        return await self.async_step_reconfigure_bluetooth()

    def _reconfigure_entry(self) -> config_entries.ConfigEntry:
        """Return the entry being reconfigured."""
        return self.hass.config_entries.async_get_entry(self.context["entry_id"])

    async def _async_apply_reconfigure(
        self,
        entry: config_entries.ConfigEntry,
        data_updates: dict[str, Any],
        unique_id: str | None = None,
    ) -> FlowResult:
        """Apply reconfigured data, reload the entry and finish the flow."""
        kwargs: dict[str, Any] = {"data": {**entry.data, **data_updates}}
        if unique_id is not None:
            kwargs["unique_id"] = unique_id
        self.hass.config_entries.async_update_entry(entry, **kwargs)
        await self.hass.config_entries.async_reload(entry.entry_id)
        return self.async_abort(reason="reconfigure_successful")

    async def async_step_reconfigure_bluetooth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Change the Bluetooth address of an existing entry."""
        entry = self._reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            new_id = user_input[CONF_RAPT_DEVICE_ID].strip().upper()
            if not new_id or new_id == "MANUAL":
                errors["base"] = "invalid_device"
            elif any(
                other.unique_id == new_id and other.entry_id != entry.entry_id
                for other in self._async_current_entries()
            ):
                return self.async_abort(reason="already_configured")
            else:
                return await self._async_apply_reconfigure(
                    entry, {CONF_RAPT_DEVICE_ID: new_id}, unique_id=new_id
                )

        return self.async_show_form(
            step_id="reconfigure_bluetooth",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_RAPT_DEVICE_ID,
                        default=entry.data.get(CONF_RAPT_DEVICE_ID),
                    ): cv.string
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Change the source entities of an existing entry."""
        entry = self._reconfigure_entry()

        if user_input is not None:
            return await self._async_apply_reconfigure(entry, user_input)

        return self.async_show_form(
            step_id="reconfigure_entity",
            data_schema=_entity_schema(dict(entry.data)),
        )

    async def async_step_reconfigure_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Change the RAPT cloud credentials of an existing entry."""
        entry = self._reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_API_EMAIL].strip()
            api_secret = user_input[CONF_API_SECRET].strip()
            error, _hydrometers = await _async_validate_cloud_credentials(
                self.hass, email, api_secret
            )
            if error:
                errors = error
            else:
                return await self._async_apply_reconfigure(
                    entry,
                    {CONF_API_EMAIL: email, CONF_API_SECRET: api_secret},
                )

        return self.async_show_form(
            step_id="reconfigure_cloud",
            data_schema=_cloud_credentials_schema(dict(entry.data)),
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Discovery helpers
    # ------------------------------------------------------------------

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

    def _merged(self, user_input: dict[str, Any]) -> dict[str, Any]:
        """Merge new option values over the existing options."""
        return {**self.config_entry.options, **user_input}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Choose what to configure."""
        menu = ["notifications", "alerts", "temperature_control", "display"]
        if self.config_entry.data.get(CONF_SOURCE_TYPE) == SOURCE_TYPE_ENTITY:
            menu.append("entities")
        return self.async_show_menu(step_id="init", menu_options=menu)

    async def async_step_notifications(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage notification options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=self._merged(user_input))

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

    async def async_step_alerts(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage alert threshold options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=self._merged(user_input))

        options = self.config_entry.options
        offline_default = (
            DEFAULT_OFFLINE_TIMEOUT_MINUTES_CLOUD
            if self.config_entry.data.get(CONF_SOURCE_TYPE) == SOURCE_TYPE_CLOUD
            else DEFAULT_OFFLINE_TIMEOUT_MINUTES
        )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_STUCK_FERMENTATION_HOURS,
                    default=options.get(
                        CONF_STUCK_FERMENTATION_HOURS, DEFAULT_STUCK_FERMENTATION_HOURS
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1, max=240, step=1, unit_of_measurement="h",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_TEMPERATURE_HIGH_THRESHOLD,
                    default=options.get(
                        CONF_TEMPERATURE_HIGH_THRESHOLD, DEFAULT_TEMPERATURE_HIGH_THRESHOLD
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=-10, max=60, step=0.5, unit_of_measurement="°C",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_TEMPERATURE_LOW_THRESHOLD,
                    default=options.get(
                        CONF_TEMPERATURE_LOW_THRESHOLD, DEFAULT_TEMPERATURE_LOW_THRESHOLD
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=-10, max=60, step=0.5, unit_of_measurement="°C",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_LOW_BATTERY_THRESHOLD,
                    default=options.get(
                        CONF_LOW_BATTERY_THRESHOLD, DEFAULT_LOW_BATTERY_THRESHOLD
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=100, step=1, unit_of_measurement="%",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_OFFLINE_TIMEOUT_MINUTES,
                    default=options.get(CONF_OFFLINE_TIMEOUT_MINUTES, offline_default),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1, max=1440, step=1, unit_of_measurement="min",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(step_id="alerts", data_schema=schema)

    async def async_step_temperature_control(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure the heater/cooler outputs and control tuning."""
        if user_input is not None:
            # An unset entity selector is omitted entirely, so clear the
            # stored value rather than leaving the previous output wired up.
            merged = self._merged(user_input)
            for key in (CONF_HEATER_SWITCH, CONF_COOLER_SWITCH):
                if key not in user_input:
                    merged.pop(key, None)
            return self.async_create_entry(title="", data=merged)

        options = self.config_entry.options

        def _entity_default(key: str) -> Any:
            return options.get(key) or vol.UNDEFINED

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_HEATER_SWITCH, default=_entity_default(CONF_HEATER_SWITCH)
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=_OUTPUT_DOMAINS)
                ),
                vol.Optional(
                    CONF_COOLER_SWITCH, default=_entity_default(CONF_COOLER_SWITCH)
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=_OUTPUT_DOMAINS)
                ),
                vol.Required(
                    CONF_HEAT_PROPORTIONAL_BAND,
                    default=options.get(
                        CONF_HEAT_PROPORTIONAL_BAND, DEFAULT_HEAT_PROPORTIONAL_BAND
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.2, max=10, step=0.1, unit_of_measurement="°C",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_HEAT_CYCLE_MINUTES,
    CONF_HEAT_INTEGRAL_HOURS,
                    default=options.get(CONF_HEAT_CYCLE_MINUTES, DEFAULT_HEAT_CYCLE_MINUTES),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=2, max=60, step=1, unit_of_measurement="min",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_HEAT_INTEGRAL_HOURS,
                    default=options.get(
                        CONF_HEAT_INTEGRAL_HOURS, DEFAULT_HEAT_INTEGRAL_HOURS
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=24, step=0.5, unit_of_measurement="h",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_COOL_DEADBAND,
                    default=options.get(CONF_COOL_DEADBAND, DEFAULT_COOL_DEADBAND),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.1, max=5, step=0.1, unit_of_measurement="°C",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_COOL_MIN_ON_MINUTES,
                    default=options.get(CONF_COOL_MIN_ON_MINUTES, DEFAULT_COOL_MIN_ON_MINUTES),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=60, step=1, unit_of_measurement="min",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_COOL_MIN_OFF_MINUTES,
                    default=options.get(CONF_COOL_MIN_OFF_MINUTES, DEFAULT_COOL_MIN_OFF_MINUTES),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=60, step=1, unit_of_measurement="min",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_CHANGEOVER_MINUTES,
                    default=options.get(CONF_CHANGEOVER_MINUTES, DEFAULT_CHANGEOVER_MINUTES),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=120, step=1, unit_of_measurement="min",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_MAX_HEAT_OVERSHOOT,
                    default=options.get(CONF_MAX_HEAT_OVERSHOOT, DEFAULT_MAX_HEAT_OVERSHOOT),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.1, max=10, step=0.1, unit_of_measurement="°C",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_ABSOLUTE_MAX_TEMPERATURE,
                    default=options.get(
                        CONF_ABSOLUTE_MAX_TEMPERATURE, DEFAULT_ABSOLUTE_MAX_TEMPERATURE
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=5, max=45, step=0.5, unit_of_measurement="°C",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(step_id="temperature_control", data_schema=schema)

    async def async_step_display(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage display and calibration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=self._merged(user_input))

        options = self.config_entry.options

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_GRAVITY_UNIT,
                    default=options.get(CONF_GRAVITY_UNIT, GRAVITY_UNIT_SG),
                ): vol.In(
                    {
                        GRAVITY_UNIT_SG: "Specific gravity (SG)",
                        GRAVITY_UNIT_PLATO: "Degrees Plato (°P)",
                    }
                ),
                vol.Required(
                    CONF_GRAVITY_OFFSET,
                    default=options.get(CONF_GRAVITY_OFFSET, 0.0),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=-0.050, max=0.050, step=0.001, unit_of_measurement="SG",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_TEMPERATURE_OFFSET,
                    default=options.get(CONF_TEMPERATURE_OFFSET, 0.0),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=-5.0, max=5.0, step=0.1, unit_of_measurement="°C",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(step_id="display", data_schema=schema)

    async def async_step_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Reconfigure the source entities."""
        if user_input is not None:
            new_data = {**self.config_entry.data, **user_input}
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data
            )
            # The entry update listener reloads the entry; keep options as-is
            return self.async_create_entry(
                title="", data=dict(self.config_entry.options)
            )

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
