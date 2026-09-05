"""Tests for the fermentation temperature control law."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from rapt_brewing.control import (
    MODE_COOL,
    MODE_HEAT,
    MODE_HEAT_COOL,
    MODE_OFF,
    ControlConfig,
    FermentationController,
    config_from_options,
)

START = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)


def _at(seconds: float) -> datetime:
    return START + timedelta(seconds=seconds)


def _heater_controller(**overrides) -> FermentationController:
    overrides.setdefault("heat_integral_hours", 0.0)
    config = ControlConfig(
        heat_proportional_band=1.0,
        heat_cycle_seconds=900.0,
        **overrides,
    )
    return FermentationController(config)


def _settle(controller: FermentationController, temperature: float, target: float,
            hours: float, mode: str = MODE_HEAT, start: float = 0.0) -> float:
    """Run the controller at a fixed temperature and return the final duty."""
    duty = 0.0
    for step in range(int(start), int(start + hours * 3600), 30):
        duty = controller.tick(_at(step), temperature, target, mode).duty
    return duty


def test_off_mode_keeps_everything_off():
    controller = _heater_controller()
    decision = controller.tick(START, temperature=15.0, target=20.0, mode=MODE_OFF)
    assert (decision.heater, decision.cooler) == (False, False)
    assert decision.reason == "off"


def test_hold_off_reason_wins_over_demand():
    controller = _heater_controller()
    decision = controller.tick(
        START, temperature=15.0, target=20.0, mode=MODE_HEAT,
        hold_off_reason="sensor data stale",
    )
    assert decision.heater is False
    assert decision.reason == "sensor data stale"


def test_missing_readings_keep_the_heater_off():
    controller = _heater_controller()
    assert controller.tick(START, None, 20.0, MODE_HEAT).heater is False
    assert controller.tick(START, 15.0, None, MODE_HEAT).heater is False


def test_full_duty_well_below_target():
    controller = _heater_controller()
    decision = controller.tick(START, temperature=17.0, target=20.0, mode=MODE_HEAT)
    assert decision.heater is True
    assert decision.duty == 1.0


def test_half_duty_switches_off_midway_through_the_window():
    controller = _heater_controller()
    decision = controller.tick(START, temperature=19.5, target=20.0, mode=MODE_HEAT)
    assert decision.heater is True
    assert decision.duty == 0.5

    # Still on just before the half-window boundary, off just after.
    assert controller.tick(_at(440), 19.5, 20.0, MODE_HEAT).heater is True
    assert controller.tick(_at(460), 19.5, 20.0, MODE_HEAT).heater is False

    # New window starts after the full cycle window elapses.
    assert controller.tick(_at(905), 19.5, 20.0, MODE_HEAT).heater is True


def test_tiny_duty_is_rounded_away():
    # 0.05 °C below target over a 900 s window is a 45 s pulse - not worth
    # switching a relay for.
    controller = _heater_controller()
    decision = controller.tick(START, temperature=19.95, target=20.0, mode=MODE_HEAT)
    assert decision.duty == 0.0
    assert decision.heater is False


def test_near_full_duty_is_rounded_up_to_continuous():
    controller = _heater_controller()
    decision = controller.tick(START, temperature=19.05, target=20.0, mode=MODE_HEAT)
    assert decision.duty == 1.0


def test_duty_is_held_for_the_rest_of_the_window():
    controller = _heater_controller()
    controller.tick(START, temperature=19.5, target=20.0, mode=MODE_HEAT)
    # Temperature reaches target mid-window; the duty only changes at the
    # next window boundary so pulses can't be chopped into fragments.
    assert controller.tick(_at(120), 20.0, 20.0, MODE_HEAT).duty == 0.5
    assert controller.tick(_at(910), 20.0, 20.0, MODE_HEAT).duty == 0.0


def test_heating_stops_above_the_overshoot_limit():
    controller = _heater_controller(max_heat_overshoot=2.0)
    decision = controller.tick(START, temperature=22.5, target=20.0, mode=MODE_HEAT)
    assert decision.heater is False
    assert decision.reason == "over temperature cutout"


def test_absolute_maximum_overrides_a_high_setpoint():
    controller = _heater_controller(absolute_max_temperature=30.0)
    decision = controller.tick(START, temperature=30.5, target=35.0, mode=MODE_HEAT)
    assert decision.heater is False


def test_cooling_hysteresis():
    controller = FermentationController(
        ControlConfig(cool_deadband=0.5, cool_min_on_seconds=0, cool_min_off_seconds=0)
    )
    # Inside the deadband: idle.
    assert controller.tick(START, 20.3, 20.0, MODE_COOL).cooler is False
    # Above the deadband: cool.
    assert controller.tick(_at(60), 20.6, 20.0, MODE_COOL).cooler is True
    # Keeps cooling until it reaches the target, not just the deadband.
    assert controller.tick(_at(120), 20.3, 20.0, MODE_COOL).cooler is True
    assert controller.tick(_at(180), 20.0, 20.0, MODE_COOL).cooler is False


def test_compressor_minimum_off_time():
    controller = FermentationController(
        ControlConfig(cool_deadband=0.5, cool_min_on_seconds=0, cool_min_off_seconds=300)
    )
    controller.tick(START, 21.0, 20.0, MODE_COOL)
    controller.tick(_at(60), 19.9, 20.0, MODE_COOL)
    assert controller.cooler_on is False

    # Demand returns immediately, but the compressor must rest first.
    assert controller.tick(_at(120), 21.0, 20.0, MODE_COOL).cooler is False
    assert controller.tick(_at(400), 21.0, 20.0, MODE_COOL).cooler is True


def test_compressor_minimum_on_time():
    controller = FermentationController(
        ControlConfig(cool_deadband=0.5, cool_min_on_seconds=180, cool_min_off_seconds=0)
    )
    assert controller.tick(START, 21.0, 20.0, MODE_COOL).cooler is True
    # Target reached almost immediately; keep running to avoid a short cycle.
    assert controller.tick(_at(60), 19.5, 20.0, MODE_COOL).cooler is True
    assert controller.tick(_at(200), 19.5, 20.0, MODE_COOL).cooler is False


def test_changeover_deadtime_blocks_heating_after_cooling():
    controller = FermentationController(
        ControlConfig(
            cool_deadband=0.5,
            cool_min_on_seconds=0,
            cool_min_off_seconds=0,
            changeover_seconds=600,
            heat_proportional_band=1.0,
            heat_cycle_seconds=900,
        )
    )
    controller.tick(START, 21.0, 20.0, MODE_HEAT_COOL)
    assert controller.cooler_on is True
    controller.tick(_at(60), 19.0, 20.0, MODE_HEAT_COOL)
    assert controller.cooler_on is False

    blocked = controller.tick(_at(120), 19.0, 20.0, MODE_HEAT_COOL)
    assert blocked.heater is False
    assert blocked.reason == "changeover lockout"

    assert controller.tick(_at(700), 19.0, 20.0, MODE_HEAT_COOL).heater is True


def test_heater_and_cooler_are_never_on_together():
    controller = FermentationController(
        ControlConfig(cool_deadband=0.5, cool_min_on_seconds=0, cool_min_off_seconds=0)
    )
    for seconds, temperature in ((0, 17.0), (60, 23.0), (700, 17.0), (1400, 23.0)):
        decision = controller.tick(_at(seconds), temperature, 20.0, MODE_HEAT_COOL)
        assert not (decision.heater and decision.cooler)


def test_ineffective_heater_is_reported():
    controller = _heater_controller(ineffective_after_seconds=3600, ineffective_rise=0.2)
    assert controller.tick(START, 15.0, 20.0, MODE_HEAT).heater_ineffective is False
    assert controller.tick(_at(1800), 15.0, 20.0, MODE_HEAT).heater_ineffective is False
    assert controller.tick(_at(3700), 15.0, 20.0, MODE_HEAT).heater_ineffective is True


def test_slowly_warming_heater_is_not_reported():
    controller = _heater_controller(ineffective_after_seconds=3600, ineffective_rise=0.2)
    controller.tick(START, 15.0, 20.0, MODE_HEAT)
    controller.tick(_at(1800), 15.3, 20.0, MODE_HEAT)
    assert controller.tick(_at(3700), 15.6, 20.0, MODE_HEAT).heater_ineffective is False


def test_config_from_options_converts_minutes_to_seconds():
    config = config_from_options(
        {
            "heat_proportional_band": 1.5,
            "heat_cycle_minutes": 20,
            "cool_min_off_minutes": 7,
            "changeover_minutes": 12,
        }
    )
    assert config.heat_proportional_band == 1.5
    assert config.heat_cycle_seconds == 1200
    assert config.cool_min_off_seconds == 420
    assert config.changeover_seconds == 720


def test_config_from_options_uses_defaults_when_empty():
    config = config_from_options({})
    assert config.heat_cycle_seconds == 900
    assert config.absolute_max_temperature == 30.0


def test_integral_trims_out_proportional_droop():
    # Proportional-only control needs half the band as permanent error to
    # hold 50% duty; the integral raises the duty at a fixed temperature.
    proportional = _heater_controller(heat_integral_hours=0.0)
    assert _settle(proportional, 19.5, 20.0, hours=6) == 0.5

    with_integral = _heater_controller(heat_integral_hours=2.0)
    assert _settle(with_integral, 19.5, 20.0, hours=6) == 1.0


def test_integral_is_dropped_while_control_is_off():
    controller = _heater_controller(heat_integral_hours=2.0)
    _settle(controller, 19.5, 20.0, hours=4)
    assert controller.tick(_at(4 * 3600), 19.5, 20.0, MODE_OFF).duty == 0.0
    # Back on: the duty starts from the proportional term alone again.
    assert controller.tick(_at(4 * 3600 + 30), 19.5, 20.0, MODE_HEAT).duty == 0.5


def test_integral_does_not_wind_up_while_saturated():
    controller = _heater_controller(heat_integral_hours=2.0)
    _settle(controller, 10.0, 20.0, hours=12)  # belt pinned on, never reaches target
    # Arriving at the setpoint must leave the heater idle. Integrating while
    # the duty is already saturated would bank enough trim to hold it on and
    # overshoot instead.
    assert _settle(controller, 20.0, 20.0, hours=2, start=12 * 3600) == 0.0


def test_backwards_clock_step_starts_a_new_window():
    controller = _heater_controller()
    assert controller.tick(_at(7200), 17.0, 20.0, MODE_HEAT).duty == 1.0
    # Clock corrected backwards: the stale window must not pin the output.
    assert controller.tick(_at(0), 19.95, 20.0, MODE_HEAT).duty == 0.0
