"""Services for RAPT Brewing integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

if TYPE_CHECKING:
    from .coordinator import RAPTBrewingCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_START_SESSION = "start_session"
SERVICE_STOP_SESSION = "stop_session"
SERVICE_ADD_SESSION_NOTE = "add_session_note"

ATTR_DEVICE_ID = "device_id"

START_SESSION_SCHEMA = vol.Schema(
    {
        vol.Required("session_name"): cv.string,
        vol.Optional("recipe"): cv.string,
        vol.Optional("original_gravity"): vol.Coerce(float),
        vol.Optional("target_gravity"): vol.Coerce(float),
        vol.Optional("target_temperature"): vol.Coerce(float),
        vol.Optional(ATTR_DEVICE_ID): cv.string,
    }
)

STOP_SESSION_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_DEVICE_ID): cv.string,
    }
)

ADD_SESSION_NOTE_SCHEMA = vol.Schema(
    {
        vol.Required("note"): cv.string,
        vol.Optional(ATTR_DEVICE_ID): cv.string,
    }
)


def _resolve_coordinator(hass: HomeAssistant, call: ServiceCall) -> RAPTBrewingCoordinator:
    """Find the coordinator the service call targets."""
    entries = [
        entry for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state is ConfigEntryState.LOADED
    ]
    if not entries:
        raise ServiceValidationError("No RAPT Brewing integration is loaded")

    device_id = call.data.get(ATTR_DEVICE_ID)
    if device_id:
        device = dr.async_get(hass).async_get(device_id)
        if device:
            for entry in entries:
                if entry.entry_id in device.config_entries:
                    return entry.runtime_data
        raise ServiceValidationError(
            f"Device {device_id} does not belong to a loaded RAPT Brewing entry"
        )

    if len(entries) == 1:
        return entries[0].runtime_data

    raise ServiceValidationError(
        "Multiple RAPT Brewing entries are configured; specify device_id"
    )


@callback
def async_register_services(hass: HomeAssistant) -> None:
    """Register integration services (idempotent)."""
    if hass.services.has_service(DOMAIN, SERVICE_START_SESSION):
        return

    async def handle_start_session(call: ServiceCall) -> None:
        coordinator = _resolve_coordinator(hass, call)
        session_id = await coordinator.start_session(
            name=call.data["session_name"],
            recipe=call.data.get("recipe"),
            original_gravity=call.data.get("original_gravity"),
            target_gravity=call.data.get("target_gravity"),
            target_temperature=call.data.get("target_temperature"),
        )
        _LOGGER.info("RAPT SERVICE: Started session %s", session_id)
        await coordinator.async_request_refresh()

    async def handle_stop_session(call: ServiceCall) -> None:
        coordinator = _resolve_coordinator(hass, call)
        session = coordinator.data.current_session
        if not session:
            raise ServiceValidationError("No current brewing session to stop")
        await coordinator.stop_session(session.id)
        _LOGGER.info("RAPT SERVICE: Stopped session %s", session.id)
        await coordinator.async_request_refresh()

    async def handle_add_session_note(call: ServiceCall) -> None:
        coordinator = _resolve_coordinator(hass, call)
        try:
            await coordinator.add_session_note(call.data["note"])
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        _LOGGER.info("RAPT SERVICE: Added session note")

    hass.services.async_register(
        DOMAIN, SERVICE_START_SESSION, handle_start_session, schema=START_SESSION_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_STOP_SESSION, handle_stop_session, schema=STOP_SESSION_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_ADD_SESSION_NOTE, handle_add_session_note, schema=ADD_SESSION_NOTE_SCHEMA
    )
