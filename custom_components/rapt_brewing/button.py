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
        name="Start New Session",
        icon="mdi:play-circle",
    ),
    ButtonEntityDescription(
        key="delete_session",
        name="Delete Current Session",
        icon="mdi:delete-circle",
    ),
    ButtonEntityDescription(
        key="clear_alerts",
        name="Clear Alerts",
        icon="mdi:alert-circle-check",
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
        elif self.entity_description.key == "delete_session":
            await self._delete_session()
        elif self.entity_description.key == "clear_alerts":
            await self._clear_alerts()

    async def _start_session(self) -> None:
        """Start a new brewing session."""
        # Automatically stop any existing session
        if self.coordinator.data.current_session:
            existing_session = self.coordinator.data.current_session
            _LOGGER.warning("RAPT BUTTON: Auto-stopping existing session: %s", existing_session.name)
            await self.coordinator.stop_session(existing_session.id)
            
        # This would typically open a dialog or form
        # For now, we'll create a default session
        # Create a better default name with timestamp
        import homeassistant.util.dt as dt_util
        session_name = f"Brew {dt_util.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Check if there's a custom session name from text input
        # This is a simplified approach - in a real implementation you'd want
        # to get the text input value, but for now we'll use the default
        
        session_id = await self.coordinator.start_session(
            name=session_name,
            recipe=None,
            original_gravity=None,
            target_gravity=None,
            target_temperature=None,
        )
        
        _LOGGER.warning("RAPT BUTTON: Started new session: %s", session_id)
        
        # Refresh coordinator data
        await self.coordinator.async_request_refresh()

    async def _delete_session(self) -> None:
        """Delete the current brewing session."""
        if self.coordinator.data.current_session:
            session_id = self.coordinator.data.current_session.id
            session_name = self.coordinator.data.current_session.name
            await self.coordinator.delete_session(session_id)
            _LOGGER.warning("RAPT BUTTON: Deleted session: %s (%s)", session_name, session_id)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.warning("RAPT BUTTON: Cannot delete session, no current session")
    
    async def _clear_alerts(self) -> None:
        """Clear all alerts for the current session."""
        if self.coordinator.data.current_session:
            session = self.coordinator.data.current_session
            alert_count = len([alert for alert in session.alerts if not alert.acknowledged])
            
            # Mark all alerts as acknowledged
            for alert in session.alerts:
                alert.acknowledged = True
            
            await self.coordinator._save_data()
            await self.coordinator.async_request_refresh()
            
            _LOGGER.warning("RAPT BUTTON: Cleared %d alert(s) for session: %s", 
                           alert_count, session.name)
        else:
            _LOGGER.warning("RAPT BUTTON: Cannot clear alerts, no current session")

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Always keep buttons available but check states in press method
        return True