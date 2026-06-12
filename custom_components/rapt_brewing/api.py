"""Async client for the RAPT cloud API (api.rapt.io)."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import aiohttp

_LOGGER = logging.getLogger(__name__)

TOKEN_URL = "https://id.rapt.io/connect/token"
API_BASE = "https://api.rapt.io"
TOKEN_CLIENT_ID = "rapt-user"
REQUEST_TIMEOUT = 30
# Refresh the bearer token this many seconds before it actually expires
TOKEN_EXPIRY_MARGIN = 300


class RAPTCloudError(Exception):
    """Error talking to the RAPT cloud API."""


class RAPTCloudAuthError(RAPTCloudError):
    """Authentication with the RAPT cloud failed."""


def parse_telemetry_record(record: dict[str, Any]) -> dict[str, Any]:
    """Normalise a RAPT telemetry record into sensor values.

    The API reports gravity in gravity points (1050.0 == 1.050 SG),
    temperature in °C, battery in %, and rssi in dBm.
    """
    gravity = record.get("gravity")
    if gravity is not None:
        gravity = float(gravity) / 1000.0

    temperature = record.get("temperature")
    if temperature is not None:
        temperature = float(temperature)

    battery = record.get("battery")
    if battery is not None:
        battery = int(round(float(battery)))

    rssi = record.get("rssi")
    if rssi is not None:
        rssi = int(round(float(rssi)))

    created_on = _parse_timestamp(record.get("createdOn"))

    return {
        "gravity": gravity,
        "temperature": temperature,
        "battery": battery,
        "signal_strength": rssi,
        "created_on": created_on,
        "version": record.get("version"),
    }


def _parse_timestamp(value: Any) -> datetime | None:
    """Parse an API timestamp; naive values are treated as UTC."""
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


class RAPTCloudClient:
    """Minimal async client for the RAPT cloud API."""

    def __init__(self, session: aiohttp.ClientSession, email: str, api_secret: str) -> None:
        """Initialize the client with RAPT portal credentials (email + API secret)."""
        self._session = session
        self._email = email
        self._api_secret = api_secret
        self._token: str | None = None
        self._token_expires_at: datetime | None = None

    async def _async_get_token(self) -> str:
        """Return a valid bearer token, requesting a new one if needed."""
        import aiohttp

        now = datetime.now(timezone.utc)
        if self._token and self._token_expires_at and now < self._token_expires_at:
            return self._token

        try:
            response = await self._session.post(
                TOKEN_URL,
                data={
                    "client_id": TOKEN_CLIENT_ID,
                    "grant_type": "password",
                    "username": self._email,
                    "password": self._api_secret,
                },
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            )
        except aiohttp.ClientError as err:
            raise RAPTCloudError(f"Error connecting to RAPT auth service: {err}") from err

        if response.status in (400, 401, 403):
            raise RAPTCloudAuthError(
                f"RAPT authentication failed (HTTP {response.status}); check email and API secret"
            )
        if response.status != 200:
            raise RAPTCloudError(f"RAPT auth service returned HTTP {response.status}")

        payload = await response.json()
        token = payload.get("access_token")
        if not token:
            raise RAPTCloudError("RAPT auth response did not contain an access token")

        expires_in = int(payload.get("expires_in", 3600))
        self._token = token
        self._token_expires_at = now + timedelta(seconds=max(60, expires_in - TOKEN_EXPIRY_MARGIN))
        return token

    async def _async_get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Perform an authenticated GET request."""
        import aiohttp

        token = await self._async_get_token()
        try:
            response = await self._session.get(
                f"{API_BASE}{path}",
                params=params,
                headers={"Authorization": f"Bearer {token}"},
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            )
        except aiohttp.ClientError as err:
            raise RAPTCloudError(f"Error connecting to RAPT API: {err}") from err

        if response.status == 401:
            # Token may have been revoked; force a refresh on the next call
            self._token = None
            raise RAPTCloudAuthError("RAPT API rejected the access token")
        if response.status != 200:
            raise RAPTCloudError(f"RAPT API returned HTTP {response.status} for {path}")

        return await response.json()

    async def async_get_hydrometers(self) -> list[dict[str, Any]]:
        """Return all hydrometers registered to the account."""
        result = await self._async_get("/api/Hydrometers/GetHydrometers")
        if not isinstance(result, list):
            raise RAPTCloudError("Unexpected response from GetHydrometers")
        return result

    async def async_get_latest_telemetry(self, hydrometer_id: str) -> dict[str, Any] | None:
        """Return the most recent telemetry record for a hydrometer (last 24h)."""
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=1)
        records = await self._async_get(
            "/api/Hydrometers/GetTelemetry",
            params={
                "hydrometerId": hydrometer_id,
                "startDate": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "endDate": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )
        if not isinstance(records, list) or not records:
            return None
        return parse_telemetry_record(records[-1])
