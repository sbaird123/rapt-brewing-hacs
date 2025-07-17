"""Button entities for RAPT Brewing integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import RAPTBrewingEntity

if TYPE_CHECKING:
    from .coordinator import RAPTBrewingCoordinator

_LOGGER = logging.getLogger(__name__)

BUTTON_TYPES: tuple[ButtonEntityDescription, ...] = (
    ButtonEntityDescription(
        key="start_session",
        name="Start Brewing Session",
        icon="mdi:play-circle",
    ),
    ButtonEntityDescription(
        key="stop_session",
        name="Stop Brewing Session", 
        icon="mdi:stop-circle",
    ),
    ButtonEntityDescription(
        key="pause_session",
        name="Pause Brewing Session",
        icon="mdi:pause-circle",
    ),
    ButtonEntityDescription(
        key="resume_session",
        name="Resume Brewing Session",
        icon="mdi:play-circle",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RAPT Brewing button entities."""
    coordinator: RAPTBrewingCoordinator = entry.runtime_data
    
    entities = [
        RAPTBrewingButton(coordinator, description)
        for description in BUTTON_TYPES
    ]
    
    async_add_entities(entities)


class RAPTBrewingButton(RAPTBrewingEntity, ButtonEntity):
    """Represent a RAPT Brewing button."""

    def __init__(
        self,
        coordinator: RAPTBrewingCoordinator,
        description: ButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{description.key}"

    async def async_press(self) -> None:
        """Handle button press."""
        _LOGGER.warning("RAPT BUTTON PRESSED: %s", self.entity_description.key)
        _LOGGER.warning("RAPT BUTTON Current session: %s", 
                       self.coordinator.data.current_session.name if self.coordinator.data.current_session else "None")
        
        if self.entity_description.key == "start_session":
            await self._start_session()
        elif self.entity_description.key == "stop_session":
            await self._stop_session()
        elif self.entity_description.key == "pause_session":
            await self._pause_session()
        elif self.entity_description.key == "resume_session":
            await self._resume_session()

    async def _start_session(self) -> None:
        """Start a new brewing session."""
        if self.coordinator.data.current_session:
            _LOGGER.warning("RAPT BUTTON: Cannot start session, current session exists: %s", 
                           self.coordinator.data.current_session.name)
            return
            
        # This would typically open a dialog or form
        # For now, we'll create a default session
        session_id = await self.coordinator.start_session(
            name=f"Brewing Session {len(self.coordinator.data.sessions) + 1}",
            recipe=None,
            original_gravity=None,
            target_gravity=None,
            target_temperature=None,
        )
        
        _LOGGER.warning("RAPT BUTTON: Started new session: %s", session_id)
        
        # Refresh coordinator data
        await self.coordinator.async_request_refresh()

    async def _stop_session(self) -> None:
        """Stop the current brewing session."""
        if self.coordinator.data.current_session:
            session_id = self.coordinator.data.current_session.id
            session_name = self.coordinator.data.current_session.name
            await self.coordinator.stop_session(session_id)
            _LOGGER.warning("RAPT BUTTON: Stopped session: %s (%s)", session_name, session_id)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.warning("RAPT BUTTON: Cannot stop session, no current session")

    async def _pause_session(self) -> None:
        """Pause the current brewing session."""
        if self.coordinator.data.current_session:
            self.coordinator.data.current_session.state = "paused"
            await self.coordinator._save_data()
            await self.coordinator.async_request_refresh()

    async def _resume_session(self) -> None:
        """Resume the current brewing session."""
        if self.coordinator.data.current_session:
            self.coordinator.data.current_session.state = "active"
            await self.coordinator._save_data()
            await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Always keep buttons available but check states in press method
        return True