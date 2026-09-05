"""Fermentation temperature control for the RAPT Brewing integration.

Exposes a thermostat that reads the wort temperature from the RAPT Pill and
drives user-supplied heater and/or cooler switch entities. The control law
itself lives in control.py; this module is the Home Assistant glue.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import TYPE_CHECKING, Any

import homeassistant.util.dt as dt_util
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    ALERT_TYPE_HEATER_INEFFECTIVE,
    CONF_COOLER_SWITCH,
    CONF_HEATER_SWITCH,
    CONTROL_TICK_SECONDS,
    SESSION_STATE_ACTIVE,
)
from .control import (
    MODE_COOL,
    MODE_HEAT,
    MODE_HEAT_COOL,
    MODE_OFF,
    FermentationController,
    config_from_options,
)
from .entity import RAPTBrewingEntity

if TYPE_CHECKING:
    from .coordinator import RAPTBrewingCoordinator

_LOGGER = logging.getLogger(__name__)

HA_DOMAIN = "homeassistant"

MODE_TO_HVAC = {
    MODE_OFF: HVACMode.OFF,
    MODE_HEAT: HVACMode.HEAT,
    MODE_COOL: HVACMode.COOL,
    MODE_HEAT_COOL: HVACMode.HEAT_COOL,
}
HVAC_TO_MODE = {hvac: mode for mode, hvac in MODE_TO_HVAC.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the fermentation thermostat when an output is configured."""
    coordinator: RAPTBrewingCoordinator = entry.runtime_data

    heater = entry.options.get(CONF_HEATER_SWITCH) or None
    cooler = entry.options.get(CONF_COOLER_SWITCH) or None
    if not heater and not cooler:
        _LOGGER.debug("RAPT CLIMATE: No heater or cooler configured, skipping setup")
        return

    async_add_entities([RAPTFermentationThermostat(coordinator, entry, heater, cooler)])


class RAPTFermentationThermostat(RAPTBrewingEntity, ClimateEntity, RestoreEntity):
    """Thermostat that holds the wort at the session's target temperature."""

    _attr_name = "Fermentation Control"
    _attr_icon = "mdi:thermostat"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.1
    _attr_min_temp = 0.0
    _attr_max_temp = 40.0
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    # Harmless on Home Assistant versions that no longer read it.
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(
        self,
        coordinator: RAPTBrewingCoordinator,
        entry: ConfigEntry,
        heater_entity_id: str | None,
        cooler_entity_id: str | None,
    ) -> None:
        """Initialize the thermostat."""
        super().__init__(coordinator, entry, "fermentation_control")
        self._heater_entity_id = heater_entity_id
        self._cooler_entity_id = cooler_entity_id
        self._controller = FermentationController(config_from_options(dict(entry.options)))
        self._attr_hvac_mode = HVACMode.OFF
        # The timer tick and coordinator updates can land together; the
        # control law must not be evaluated twice at once.
        self._control_lock = asyncio.Lock()

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Modes available given which outputs are configured."""
        modes = [HVACMode.OFF]
        if self._heater_entity_id:
            modes.append(HVACMode.HEAT)
        if self._cooler_entity_id:
            modes.append(HVACMode.COOL)
        if self._heater_entity_id and self._cooler_entity_id:
            modes.append(HVACMode.HEAT_COOL)
        return modes

    @property
    def current_temperature(self) -> float | None:
        """Wort temperature from the RAPT Pill."""
        session = self.coordinator.data.current_session
        return session.current_temperature if session else None

    @property
    def target_temperature(self) -> float | None:
        """Setpoint, shared with the Target Temperature number entity."""
        session = self.coordinator.data.current_session
        return session.target_temperature if session else None

    @property
    def hvac_action(self) -> HVACAction:
        """What the thermostat is doing right now."""
        if self._attr_hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        if self._controller.cooler_on:
            return HVACAction.COOLING
        if self._controller.heater_on:
            return HVACAction.HEATING
        return HVACAction.IDLE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the control decision for dashboards and debugging."""
        return {
            "heater_entity_id": self._heater_entity_id,
            "cooler_entity_id": self._cooler_entity_id,
            "heater_duty_cycle": round(self._controller.duty * 100, 1),
            "control_reason": self._controller.reason,
        }

    @property
    def available(self) -> bool:
        """The thermostat stays available so its mode can always be changed."""
        return True

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def async_added_to_hass(self) -> None:
        """Restore the mode and start the control loop."""
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state and last_state.state in self.hvac_modes:
            self._attr_hvac_mode = HVACMode(last_state.state)

        # Adopt whatever the outputs are actually doing after a restart, so a
        # fridge that was left running still gets its minimum on time before
        # the first tick can stop it again.
        self._controller.note_external_change(
            dt_util.utcnow(),
            self._output_is_on(self._heater_entity_id),
            self._output_is_on(self._cooler_entity_id),
        )

        self.async_on_remove(
            async_track_time_interval(
                self.hass,
                self._async_control_tick,
                timedelta(seconds=CONTROL_TICK_SECONDS),
            )
        )
        await self._async_control()

    async def async_will_remove_from_hass(self) -> None:
        """Never leave a heater running when the entity goes away."""
        await self._async_set_output(self._heater_entity_id, False)
        await self._async_set_output(self._cooler_entity_id, False)
        await super().async_will_remove_from_hass()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Re-evaluate as soon as a new reading lands."""
        self.hass.async_create_task(self._async_control())
        super()._handle_coordinator_update()

    async def _async_control_tick(self, _now: Any) -> None:
        """Timer callback for the control loop."""
        await self._async_control()

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------

    async def _async_control(self) -> None:
        """Evaluate the control law and drive the outputs."""
        async with self._control_lock:
            await self._async_control_locked()

    async def _async_control_locked(self) -> None:
        """Evaluate the control law; callers must hold the control lock."""
        mode = HVAC_TO_MODE.get(self._attr_hvac_mode, MODE_OFF)
        session = self.coordinator.data.current_session

        hold_off_reason: str | None = None
        if mode != MODE_OFF:
            if session is None or session.state != SESSION_STATE_ACTIVE:
                hold_off_reason = "no active session"
            elif not self.coordinator.is_online:
                hold_off_reason = "sensor data stale"

        decision = self._controller.tick(
            dt_util.utcnow(),
            session.current_temperature if session else None,
            session.target_temperature if session else None,
            mode,
            hold_off_reason,
        )

        await self._async_set_output(self._heater_entity_id, decision.heater)
        await self._async_set_output(self._cooler_entity_id, decision.cooler)

        if decision.heater_ineffective and session is not None:
            await self.coordinator.async_add_alert(
                session,
                ALERT_TYPE_HEATER_INEFFECTIVE,
                "Heater has run continuously without warming the wort - "
                "check that it is plugged in and powerful enough for the ambient temperature",
            )

        self.async_write_ha_state()

    def _output_is_on(self, entity_id: str | None) -> bool:
        """Return whether an output entity is currently switched on."""
        if not entity_id:
            return False
        state = self.hass.states.get(entity_id)
        return state is not None and state.state == STATE_ON

    async def _async_set_output(self, entity_id: str | None, should_be_on: bool) -> None:
        """Switch an output entity, skipping the call when already correct."""
        if not entity_id:
            return

        state = self.hass.states.get(entity_id)
        if state is not None and (state.state == STATE_ON) == should_be_on:
            return

        try:
            await self.hass.services.async_call(
                HA_DOMAIN,
                SERVICE_TURN_ON if should_be_on else SERVICE_TURN_OFF,
                {ATTR_ENTITY_ID: entity_id},
                blocking=True,
            )
        except Exception as err:  # noqa: BLE001 - never let an output failure break the loop
            _LOGGER.warning("RAPT CLIMATE: Failed to switch %s: %s", entity_id, err)

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Change the control mode."""
        if hvac_mode not in self.hvac_modes:
            _LOGGER.warning("RAPT CLIMATE: Unsupported HVAC mode: %s", hvac_mode)
            return
        self._attr_hvac_mode = hvac_mode
        _LOGGER.info("RAPT CLIMATE: Mode set to %s", hvac_mode)
        await self._async_control()

    async def async_turn_on(self) -> None:
        """Resume control in the richest mode the outputs allow."""
        for mode in (HVACMode.HEAT_COOL, HVACMode.HEAT, HVACMode.COOL):
            if mode in self.hvac_modes:
                await self.async_set_hvac_mode(mode)
                return

    async def async_turn_off(self) -> None:
        """Stop controlling and switch the outputs off."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the session's target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        session = self.coordinator.data.current_session
        if session is None:
            _LOGGER.warning("RAPT CLIMATE: Cannot set target temperature, no current session")
            return

        session.target_temperature = float(temperature)
        _LOGGER.info(
            "RAPT CLIMATE: Set target temperature to %.1f°C for session: %s",
            temperature, session.name,
        )
        await self.coordinator.async_save_data()
        await self._async_control()
        await self.coordinator.async_request_refresh()
