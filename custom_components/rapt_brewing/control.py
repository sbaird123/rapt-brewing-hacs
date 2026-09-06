"""Fermentation temperature control logic.

Deliberately free of Home Assistant imports so the control law can be unit
tested with a fake clock. The Home Assistant glue (reading the wort
temperature, switching the heater/cooler entities) lives in climate.py.

Heating uses time-proportional (PWM) control rather than simple hysteresis:
a fermenter heat belt is typically 25-50 W and heats the vessel wall, so
there is 30-60 minutes of dead time before the Pill floating in the wort
sees the change. Bang-bang control on that plant overshoots and wanders.

Cooling uses hysteresis with minimum on/off times, because a fridge
compressor must never be short cycled.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

MODE_OFF = "off"
MODE_HEAT = "heat"
MODE_COOL = "cool"
MODE_HEAT_COOL = "heat_cool"

# Never command an output for less than this; shorter pulses do nothing
# useful thermally and just wear out the relay in a smart plug.
MIN_PULSE_SECONDS = 60


@dataclass
class ControlConfig:
    """Tuning parameters for the fermentation controller."""

    # Heating (time proportional plus a slow integral trim)
    heat_proportional_band: float = 1.0  # °C below target for 100% duty
    heat_cycle_seconds: float = 900.0  # PWM window length
    heat_integral_hours: float = 2.0  # time to trim out steady-state droop; 0 disables

    # Cooling (hysteresis, compressor friendly)
    cool_deadband: float = 0.5  # °C above target before cooling starts
    cool_min_on_seconds: float = 180.0
    cool_min_off_seconds: float = 300.0

    # Shared safety limits
    changeover_seconds: float = 600.0  # deadtime between heating and cooling
    max_heat_overshoot: float = 2.0  # never heat above target + this
    absolute_max_temperature: float = 30.0  # hard cutout regardless of target

    # Heater effectiveness watchdog
    ineffective_after_seconds: float = 7200.0  # duty pinned at 100% this long
    ineffective_rise: float = 0.2  # with less than this much °C of rise


@dataclass
class ControlDecision:
    """The controller's requested output states for one tick."""

    heater: bool
    cooler: bool
    duty: float
    reason: str
    heater_ineffective: bool = False


class FermentationController:
    """Decide heater/cooler output states from the wort temperature."""

    def __init__(self, config: ControlConfig | None = None) -> None:
        """Initialize the controller with all outputs off."""
        self.config = config or ControlConfig()
        self.heater_on = False
        self.cooler_on = False
        self.duty = 0.0
        self.reason = "off"
        self._heater_changed_at: datetime | None = None
        self._cooler_changed_at: datetime | None = None
        self._window_started_at: datetime | None = None
        self._window_duty = 0.0
        self._integral = 0.0
        self._saturated_since: datetime | None = None
        self._saturated_temperature: float | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def tick(
        self,
        now: datetime,
        temperature: float | None,
        target: float | None,
        mode: str,
        hold_off_reason: str | None = None,
    ) -> ControlDecision:
        """Evaluate the control law and return the requested output states.

        `hold_off_reason` lets the caller force everything off with a
        meaningful reason (no active session, stale sensor data, ...).
        """
        if hold_off_reason or mode == MODE_OFF or temperature is None or target is None:
            self._reset_window()
            if hold_off_reason:
                reason = hold_off_reason
            elif mode == MODE_OFF:
                reason = "thermostat off"
            elif temperature is None:
                reason = "no temperature reading"
            else:
                reason = "no target temperature"
            return self._apply(now, False, False, 0.0, reason)

        cfg = self.config
        heat_allowed = mode in (MODE_HEAT, MODE_HEAT_COOL)
        cool_allowed = mode in (MODE_COOL, MODE_HEAT_COOL)

        over_absolute_max = temperature >= cfg.absolute_max_temperature
        block_heat = over_absolute_max or temperature > target + cfg.max_heat_overshoot

        want_heat = False
        if heat_allowed and not block_heat:
            want_heat = self._heater_window_state(now, temperature, target)
        else:
            self._reset_window()

        want_cool = False
        if cool_allowed:
            want_cool = self._cooling_wanted(now, temperature, target, force=over_absolute_max)

        # Never run both; cooling wins because it is the safety direction.
        if want_cool:
            want_heat = False
            self._reset_window()

        # Changeover deadtime so the two outputs can't fight across a swing.
        if want_heat and self._seconds_since(self._cooler_changed_at, now) < cfg.changeover_seconds:
            want_heat = False
            self._reset_window()
            return self._apply(now, False, False, 0.0, "changeover lockout")
        if want_cool and self._seconds_since(self._heater_changed_at, now) < cfg.changeover_seconds:
            return self._apply(now, False, False, 0.0, "changeover lockout")

        ineffective = self._track_effectiveness(now, temperature, heat_allowed and not block_heat)

        if want_cool:
            reason = "cooling (over temperature cutout)" if over_absolute_max else "cooling"
        elif block_heat and heat_allowed:
            reason = "over temperature cutout"
        elif want_heat:
            reason = f"heating at {self._window_duty:.0%} duty"
        elif heat_allowed and self._window_duty > 0:
            reason = f"heating off phase ({self._window_duty:.0%} duty)"
        else:
            reason = "idle"

        return self._apply(now, want_heat, want_cool, self._window_duty, reason, ineffective)

    def note_external_change(self, now: datetime, heater_on: bool, cooler_on: bool) -> None:
        """Sync internal state with the real switches after a restart."""
        self.heater_on = heater_on
        self.cooler_on = cooler_on
        self._heater_changed_at = now if heater_on else None
        self._cooler_changed_at = now if cooler_on else None

    # ------------------------------------------------------------------
    # Heating
    # ------------------------------------------------------------------

    def _heater_duty(self, temperature: float, target: float) -> float:
        """Proportional-plus-integral duty for the next PWM window.

        Proportional-only control droops: holding 50% duty needs half the
        band as permanent error, so a 25 W belt would settle around 0.5 °C
        under setpoint. The integral term trims that out over a couple of
        hours, which is slow enough not to fight the fermenter's own lag.
        """
        cfg = self.config
        band = max(cfg.heat_proportional_band, 0.1)
        error = target - temperature
        raw = (error + self._integral) / band
        duty = min(1.0, max(0.0, raw))

        if cfg.heat_integral_hours > 0:
            saturated = (raw >= 1.0 and error > 0) or (raw <= 0.0 and error < 0)
            if not saturated:
                step = error * (cfg.heat_cycle_seconds / 3600.0) / cfg.heat_integral_hours
                self._integral = min(band, max(-band, self._integral + step))

        return duty

    def _quantise_duty(self, duty: float) -> float:
        """Round a duty that would produce a useless pulse to full off/on."""
        window = self.config.heat_cycle_seconds
        if duty * window < MIN_PULSE_SECONDS:
            return 0.0
        if (1.0 - duty) * window < MIN_PULSE_SECONDS:
            return 1.0
        return duty

    def _heater_window_state(self, now: datetime, temperature: float, target: float) -> bool:
        """Return whether the heater should be on within the current window.

        The duty is recomputed only at window boundaries; letting it move
        mid-window would chop the pulse into fragments shorter than
        MIN_PULSE_SECONDS.
        """
        window = self.config.heat_cycle_seconds
        elapsed = self._seconds_since(self._window_started_at, now)
        if self._window_started_at is None or elapsed >= window:
            self._window_started_at = now
            self._window_duty = self._quantise_duty(self._heater_duty(temperature, target))
            elapsed = 0.0

        return elapsed < self._window_duty * window

    def _reset_window(self) -> None:
        """Abandon the current PWM window and its accumulated integral."""
        self._window_started_at = None
        self._window_duty = 0.0
        self._integral = 0.0

    def _track_effectiveness(self, now: datetime, temperature: float, heating_allowed: bool) -> bool:
        """Detect a heater that is running flat out without warming the wort."""
        cfg = self.config
        if not heating_allowed or self._window_duty < 1.0:
            self._saturated_since = None
            self._saturated_temperature = None
            return False

        if self._saturated_since is None:
            self._saturated_since = now
            self._saturated_temperature = temperature
            return False

        if temperature - (self._saturated_temperature or temperature) >= cfg.ineffective_rise:
            # It is working, just slowly - restart the watchdog from here.
            self._saturated_since = now
            self._saturated_temperature = temperature
            return False

        return self._seconds_since(self._saturated_since, now) >= cfg.ineffective_after_seconds

    # ------------------------------------------------------------------
    # Cooling
    # ------------------------------------------------------------------

    def _cooling_wanted(
        self, now: datetime, temperature: float, target: float, force: bool
    ) -> bool:
        """Hysteresis with compressor minimum on/off times."""
        cfg = self.config
        if self.cooler_on:
            if force:
                return True
            if self._seconds_since(self._cooler_changed_at, now) < cfg.cool_min_on_seconds:
                return True
            return temperature > target
        if self._seconds_since(self._cooler_changed_at, now) < cfg.cool_min_off_seconds:
            return False
        return force or temperature > target + cfg.cool_deadband

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _apply(
        self,
        now: datetime,
        heater: bool,
        cooler: bool,
        duty: float,
        reason: str,
        heater_ineffective: bool = False,
    ) -> ControlDecision:
        """Record the decision and return it."""
        if heater != self.heater_on:
            self.heater_on = heater
            self._heater_changed_at = now
        if cooler != self.cooler_on:
            self.cooler_on = cooler
            self._cooler_changed_at = now
        self.duty = duty
        self.reason = reason
        return ControlDecision(
            heater=heater,
            cooler=cooler,
            duty=duty,
            reason=reason,
            heater_ineffective=heater_ineffective,
        )

    @staticmethod
    def _seconds_since(when: datetime | None, now: datetime) -> float:
        """Seconds since `when`, or infinity if it never happened.

        A backwards clock step (an NTP correction, say) also reports
        infinity: the stored timestamp is no longer trustworthy, so start
        the timer afresh rather than freezing the PWM window.
        """
        if when is None:
            return float("inf")
        elapsed = (now - when).total_seconds()
        return float("inf") if elapsed < 0 else elapsed


def config_from_options(options: dict) -> ControlConfig:
    """Build a ControlConfig from config entry options."""
    from .const import (
        CONF_ABSOLUTE_MAX_TEMPERATURE,
        CONF_CHANGEOVER_MINUTES,
        CONF_COOL_DEADBAND,
        CONF_COOL_MIN_OFF_MINUTES,
        CONF_COOL_MIN_ON_MINUTES,
        CONF_HEAT_CYCLE_MINUTES,
        CONF_HEAT_INTEGRAL_HOURS,
        CONF_HEAT_PROPORTIONAL_BAND,
        CONF_MAX_HEAT_OVERSHOOT,
        DEFAULT_ABSOLUTE_MAX_TEMPERATURE,
        DEFAULT_CHANGEOVER_MINUTES,
        DEFAULT_COOL_DEADBAND,
        DEFAULT_COOL_MIN_OFF_MINUTES,
        DEFAULT_COOL_MIN_ON_MINUTES,
        DEFAULT_HEAT_CYCLE_MINUTES,
        DEFAULT_HEAT_INTEGRAL_HOURS,
        DEFAULT_HEAT_PROPORTIONAL_BAND,
        DEFAULT_MAX_HEAT_OVERSHOOT,
    )

    def _minutes(key: str, default: float) -> float:
        return float(options.get(key, default)) * 60.0

    return ControlConfig(
        heat_proportional_band=float(
            options.get(CONF_HEAT_PROPORTIONAL_BAND, DEFAULT_HEAT_PROPORTIONAL_BAND)
        ),
        heat_cycle_seconds=_minutes(CONF_HEAT_CYCLE_MINUTES, DEFAULT_HEAT_CYCLE_MINUTES),
        heat_integral_hours=float(
            options.get(CONF_HEAT_INTEGRAL_HOURS, DEFAULT_HEAT_INTEGRAL_HOURS)
        ),
        cool_deadband=float(options.get(CONF_COOL_DEADBAND, DEFAULT_COOL_DEADBAND)),
        cool_min_on_seconds=_minutes(CONF_COOL_MIN_ON_MINUTES, DEFAULT_COOL_MIN_ON_MINUTES),
        cool_min_off_seconds=_minutes(CONF_COOL_MIN_OFF_MINUTES, DEFAULT_COOL_MIN_OFF_MINUTES),
        changeover_seconds=_minutes(CONF_CHANGEOVER_MINUTES, DEFAULT_CHANGEOVER_MINUTES),
        max_heat_overshoot=float(
            options.get(CONF_MAX_HEAT_OVERSHOOT, DEFAULT_MAX_HEAT_OVERSHOOT)
        ),
        absolute_max_temperature=float(
            options.get(CONF_ABSOLUTE_MAX_TEMPERATURE, DEFAULT_ABSOLUTE_MAX_TEMPERATURE)
        ),
    )
