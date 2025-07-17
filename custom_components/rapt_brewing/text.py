"""Text input entities for RAPT Brewing integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import RAPTBrewingEntity

if TYPE_CHECKING:
    from .coordinator import RAPTBrewingCoordinator

_LOGGER = logging.getLogger(__name__)

TEXT_TYPES: tuple[TextEntityDescription, ...] = (
    TextEntityDescription(
        key="session_name",
        name="Session Name",
        icon="mdi:text-box",
    ),
    TextEntityDescription(
        key="recipe_name",
        name="Recipe Name",
        icon="mdi:book-open",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RAPT Brewing text entities."""
    coordinator: RAPTBrewingCoordinator = entry.runtime_data
    
    entities = [
        RAPTBrewingText(coordinator, description)
        for description in TEXT_TYPES
    ]
    
    async_add_entities(entities)


class RAPTBrewingText(RAPTBrewingEntity, TextEntity):
    """Represent a RAPT Brewing text entity."""

    def __init__(
        self,
        coordinator: RAPTBrewingCoordinator,
        description: TextEntityDescription,
    ) -> None:
        """Initialize the text entity."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{description.key}"
        self._attr_mode = "text"
        self._attr_native_max = 100

    @property
    def native_value(self) -> str | None:
        """Return the current value."""
        if self.entity_description.key == "session_name":
            return (
                self.coordinator.data.current_session.name
                if self.coordinator.data.current_session
                else None
            )
        elif self.entity_description.key == "recipe_name":
            return (
                self.coordinator.data.current_session.recipe
                if self.coordinator.data.current_session
                else None
            )
        return None

    async def async_set_value(self, value: str) -> None:
        """Set the text value."""
        if self.entity_description.key == "session_name":
            await self._set_session_name(value)
        elif self.entity_description.key == "recipe_name":
            await self._set_recipe_name(value)

    async def _set_session_name(self, name: str) -> None:
        """Set session name."""
        if self.coordinator.data.current_session and name.strip():
            self.coordinator.data.current_session.name = name.strip()
            await self.coordinator._save_data()
            await self.coordinator.async_request_refresh()
            _LOGGER.warning("RAPT TEXT: Updated session name to: %s", name.strip())

    async def _set_recipe_name(self, recipe: str) -> None:
        """Set recipe name."""
        if self.coordinator.data.current_session:
            self.coordinator.data.current_session.recipe = recipe.strip() or None
            await self.coordinator._save_data()
            await self.coordinator.async_request_refresh()
            _LOGGER.warning("RAPT TEXT: Updated recipe name to: %s", recipe.strip())

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.data.current_session is not None