"""Diagnostics support for RAPT Brewing."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_API_EMAIL, CONF_API_SECRET, CONF_RAPT_DEVICE_ID, CONF_HYDROMETER_ID

if TYPE_CHECKING:
    from .coordinator import RAPTBrewingCoordinator
    from .data import BrewingSession

TO_REDACT = {CONF_RAPT_DEVICE_ID, CONF_API_EMAIL, CONF_API_SECRET, CONF_HYDROMETER_ID}


def _session_summary(session: BrewingSession) -> dict[str, Any]:
    """Summarise a session without dumping every data point."""
    return {
        "id": session.id,
        "name": session.name,
        "state": session.state,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "original_gravity": session.original_gravity,
        "current_gravity": session.current_gravity,
        "target_gravity": session.target_gravity,
        "current_temperature": session.current_temperature,
        "alcohol_percentage": session.alcohol_percentage,
        "attenuation": session.attenuation,
        "fermentation_rate": session.fermentation_rate,
        "data_point_count": len(session.data_points),
        "last_data_points": [dp.to_dict() for dp in session.data_points[-5:]],
        "alerts": [alert.to_dict() for alert in session.alerts],
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: RAPTBrewingCoordinator = entry.runtime_data
    current_data = coordinator.get_current_ble_data()
    last_received = coordinator.last_data_received

    return {
        "entry": {
            "title": entry.title,
            "version": entry.version,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "source_type": coordinator.source_type,
        "is_online": coordinator.is_online,
        "last_data_received": last_received.isoformat() if last_received else None,
        "offline_timeout_minutes": coordinator.offline_timeout.total_seconds() / 60,
        "signal_strength": coordinator.get_ble_signal_strength(),
        "current_data": current_data.to_dict() if current_data else None,
        "current_session_id": (
            coordinator.data.current_session.id
            if coordinator.data.current_session else None
        ),
        "sessions": [
            _session_summary(session)
            for session in coordinator.data.sessions.values()
        ],
    }
