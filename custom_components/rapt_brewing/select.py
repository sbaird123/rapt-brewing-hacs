"""Select entities for RAPT Brewing integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import RAPTBrewingEntity

if TYPE_CHECKING:
    from .coordinator import RAPTBrewingCoordinator
    from .data import BrewingSession

_LOGGER = logging.getLogger(__name__)

SESSION_SELECT = SelectEntityDescription(
    key="session",
    name="Session",
    icon="mdi:history",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RAPT Brewing select entities."""
    coordinator: RAPTBrewingCoordinator = entry.runtime_data
    async_add_entities([RAPTBrewingSessionSelect(coordinator, entry, SESSION_SELECT)])


def _session_label(session: BrewingSession) -> str:
    """Build a stable, human-readable label for a session."""
    if session.started_at:
        return f"{session.name} ({session.started_at.strftime('%Y-%m-%d %H:%M')})"
    return session.name


class RAPTBrewingSessionSelect(RAPTBrewingEntity, SelectEntity):
    """Switch which brewing session the sensors display (history browsing)."""

    def __init__(
        self,
        coordinator: RAPTBrewingCoordinator,
        entry: ConfigEntry,
        description: SelectEntityDescription,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, entry, description.key)
        self.entity_description = description

    def _sessions_by_label(self) -> dict[str, BrewingSession]:
        """Map display labels to sessions, newest first."""
        sessions = sorted(
            self.coordinator.data.sessions.values(),
            key=lambda s: s.started_at.timestamp() if s.started_at else 0.0,
            reverse=True,
        )
        return {_session_label(s): s for s in sessions}

    @property
    def options(self) -> list[str]:
        """Return all sessions, newest first."""
        return list(self._sessions_by_label())

    @property
    def current_option(self) -> str | None:
        """Return the label of the currently viewed session."""
        session = self.coordinator.data.current_session
        return _session_label(session) if session else None

    async def async_select_option(self, option: str) -> None:
        """Switch the viewed session. New data only flows into active sessions."""
        session = self._sessions_by_label().get(option)
        if session is None:
            _LOGGER.warning("RAPT SELECT: Unknown session option: %s", option)
            return
        await self.coordinator.select_session(session.id)
        _LOGGER.info("RAPT SELECT: Now viewing session: %s", session.name)

    @property
    def available(self) -> bool:
        """Available whenever any sessions exist."""
        return bool(self.coordinator.data.sessions)
