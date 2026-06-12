"""Test setup: stub the Home Assistant modules the pure modules import.

These tests exercise the dependency-free parts of the integration (BLE
parser, data model, cloud response parsing, unit conversion) without
requiring a Home Assistant installation.
"""
from __future__ import annotations

import datetime as dt
import sys
import types
from pathlib import Path

COMPONENT_DIR = Path(__file__).resolve().parent.parent / "custom_components" / "rapt_brewing"


def _ensure_module(name: str) -> types.ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    module = types.ModuleType(name)
    sys.modules[name] = module
    return module


# Minimal homeassistant stubs for the modules under test
_ha = _ensure_module("homeassistant")
_util = _ensure_module("homeassistant.util")
_dt_util = _ensure_module("homeassistant.util.dt")
_dt_util.utcnow = lambda: dt.datetime.now(dt.timezone.utc)
_dt_util.now = lambda: dt.datetime.now().astimezone()
_components = _ensure_module("homeassistant.components")
_bluetooth = _ensure_module("homeassistant.components.bluetooth")
_bluetooth.BluetoothServiceInfoBleak = object

# Expose custom_components/rapt_brewing as an importable package without
# executing its __init__.py (which needs a full Home Assistant install).
_pkg = types.ModuleType("rapt_brewing")
_pkg.__path__ = [str(COMPONENT_DIR)]
sys.modules["rapt_brewing"] = _pkg


class FakeServiceInfo:
    """Stand-in for BluetoothServiceInfoBleak."""

    def __init__(self, manufacturer_data: dict[int, bytes], address: str = "78:E3:6D:00:11:22", rssi: int = -60):
        self.manufacturer_data = manufacturer_data
        self.address = address
        self.rssi = rssi
