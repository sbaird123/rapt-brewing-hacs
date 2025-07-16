"""Select entities for RAPT Brewing integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    FERMENTATION_STAGE_PRIMARY,
    FERMENTATION_STAGE_SECONDARY,
    FERMENTATION_STAGE_CONDITIONING,
    FERMENTATION_STAGE_PACKAGING,
)
from .entity import RAPTBrewingEntity

if TYPE_CHECKING:
    from .coordinator import RAPTBrewingCoordinator

_LOGGER = logging.getLogger(__name__)

FERMENTATION_STAGES = [
    FERMENTATION_STAGE_PRIMARY,
    FERMENTATION_STAGE_SECONDARY,
    FERMENTATION_STAGE_CONDITIONING,
    FERMENTATION_STAGE_PACKAGING,
]

SELECT_TYPES: tuple[SelectEntityDescription, ...] = (
    SelectEntityDescription(
        key="fermentation_stage",
        name="Fermentation Stage",
        icon="mdi:flask",
        options=FERMENTATION_STAGES,
    ),
    SelectEntityDescription(
        key="active_session",
        name="Active Session",
        icon="mdi:beer",
        options=[],  # Will be populated dynamically
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up RAPT Brewing select entities."""
    coordinator: RAPTBrewingCoordinator = entry.runtime_data
    
    entities = [
        RAPTBrewingSelect(coordinator, description)
        for description in SELECT_TYPES
    ]
    
    async_add_entities(entities)


class RAPTBrewingSelect(RAPTBrewingEntity, SelectEntity):
    """Represent a RAPT Brewing select entity."""

    def __init__(
        self,
        coordinator: RAPTBrewingCoordinator,
        description: SelectEntityDescription,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{description.key}"

    @property
    def options(self) -> list[str]:
        """Return the list of available options."""
        if self.entity_description.key == "fermentation_stage":
            return FERMENTATION_STAGES
        elif self.entity_description.key == "active_session":
            return [
                session.name for session in self.coordinator.data.sessions.values()
                if session.state in ("active", "paused")
            ]
        return self.entity_description.options

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if self.entity_description.key == "fermentation_stage":
            return (
                self.coordinator.data.current_session.stage
                if self.coordinator.data.current_session
                else None
            )
        elif self.entity_description.key == "active_session":
            return (
                self.coordinator.data.current_session.name
                if self.coordinator.data.current_session
                else None
            )
        return None

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        if self.entity_description.key == "fermentation_stage":
            await self._select_fermentation_stage(option)
        elif self.entity_description.key == "active_session":
            await self._select_active_session(option)

    async def _select_fermentation_stage(self, stage: str) -> None:
        """Select fermentation stage."""
        if self.coordinator.data.current_session and stage in FERMENTATION_STAGES:
            self.coordinator.data.current_session.stage = stage
            await self.coordinator._save_data()
            await self.coordinator.async_request_refresh()

    async def _select_active_session(self, session_name: str) -> None:
        """Select active session."""
        for session in self.coordinator.data.sessions.values():
            if session.name == session_name and session.state in ("active", "paused"):
                self.coordinator.data.set_current_session(session.id)
                await self.coordinator._save_data()
                await self.coordinator.async_request_refresh()
                break

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if self.entity_description.key == "fermentation_stage":
            return self.coordinator.data.current_session is not None
        elif self.entity_description.key == "active_session":
            return len(self.options) > 0
        return True