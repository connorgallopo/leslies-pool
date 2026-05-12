"""API client for Leslie's Pool Water Tests."""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from .const import (
    BOOMI_BASE_URL,
    BOOMI_BASIC_USER,
    BOOMI_BASIC_PASS,
    OCAPI_BASE_URL,
    OCAPI_CLIENT_ID,
    USER_AGENT,
    CHEMISTRY_TESTS,
)

_LOGGER = logging.getLogger(__name__)


class LesliesPoolError(Exception):
    """Base error from the Leslie's API client."""


class InvalidAuthError(LesliesPoolError):
    """Email or password rejected by Leslie's."""


class PoolNotFoundError(LesliesPoolError):
    """Account has no pools, or the configured pool is gone."""


@dataclass(frozen=True)
class PoolProfile:
    """A pool returned by the Boomi poolProfiles endpoint."""

    id: str
    pool_name: str
    sanitization_code: str | None = None
    size_in_gallons: str | None = None


class LesliesPoolApi:
    """Client for the Leslie's Pool Boomi mobile API."""

    def __init__(
        self,
        relate_customer_id: str,
        email: str,
        pool_profile_id: str,
        pool_name: str,
    ) -> None:
        """Build a client for an already-configured account."""
        self._relate_customer_id = relate_customer_id
        self._email = email
        self._pool_profile_id = pool_profile_id
        self._pool_name = pool_name

        self._session = requests.Session()
        self._sanitizer_lookup: dict[str, str] | None = None
        self._last_successful_values: dict[str, Any] = {}

    def _boomi_headers(self) -> dict[str, str]:
        """Headers required on every Boomi request."""
        auth = base64.b64encode(f"{BOOMI_BASIC_USER}:{BOOMI_BASIC_PASS}".encode()).decode()
        return {
            "Authorization": f"Basic {auth}",
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "source": "APP",
            "DDP_email": self._email,
            "DDP_ID": self._relate_customer_id,
        }

    @staticmethod
    def resolve_relate_customer_id(email: str, password: str) -> tuple[str, str]:
        """Return (customer_id, relateCustomerID) for the given credentials.

        Uses the OCAPI Session Bridge. Raises InvalidAuthError on bad creds.
        """
        creds = base64.b64encode(f"{email}:{password}".encode()).decode()
        url = f"{OCAPI_BASE_URL}/customers/auth?client_id={OCAPI_CLIENT_ID}"
        r = requests.post(
            url,
            headers={
                "Authorization": f"Basic {creds}",
                "Content-Type": "application/json",
                "User-Agent": USER_AGENT,
            },
            json={"type": "credentials"},
            timeout=20,
        )
        if r.status_code == 401:
            raise InvalidAuthError("Leslie's rejected the email/password")
        r.raise_for_status()

        jwt = r.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        payload = r.json()
        customer_id = payload.get("customer_id")
        if not jwt or not customer_id:
            raise LesliesPoolError("OCAPI auth response missing JWT or customer_id")

        r = requests.get(
            f"{OCAPI_BASE_URL}/customers/{customer_id}?client_id={OCAPI_CLIENT_ID}",
            headers={
                "Authorization": f"Bearer {jwt}",
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            },
            timeout=20,
        )
        r.raise_for_status()
        relate_id = r.json().get("c_relateCustomerID")
        if not relate_id:
            raise LesliesPoolError("Customer record missing c_relateCustomerID")
        return customer_id, str(relate_id)

    @staticmethod
    def discover_pool_profiles(email: str, relate_customer_id: str) -> list[PoolProfile]:
        """Return the user's registered pools."""
        auth = base64.b64encode(f"{BOOMI_BASIC_USER}:{BOOMI_BASIC_PASS}".encode()).decode()
        r = requests.get(
            f"{BOOMI_BASE_URL}/ws/rest/Mobile/RelateORCE/poolProfiles/v1",
            headers={
                "Authorization": f"Basic {auth}",
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
                "source": "APP",
                "DDP_email": email,
                "DDP_ID": relate_customer_id,
            },
            timeout=20,
        )
        r.raise_for_status()
        raw = r.json().get("pool_profiles", [])
        if not raw:
            raise PoolNotFoundError("Account has no pool profiles")
        return [
            PoolProfile(
                id=str(p["id"]),
                pool_name=p.get("pool_name") or f"Pool {p['id']}",
                sanitization_code=str(p.get("sanitization", "")) or None,
                size_in_gallons=str(p.get("size_in_gallons", "")) or None,
            )
            for p in raw
        ]

    def _get_sanitizer_lookup(self) -> dict[str, str]:
        """Fetch and cache the brand_id -> sanitizer name map."""
        if self._sanitizer_lookup is None:
            r = self._session.get(
                f"{BOOMI_BASE_URL}/ws/rest/Mobile/poolSanitizers/v1",
                headers=self._boomi_headers(),
                timeout=20,
            )
            r.raise_for_status()
            self._sanitizer_lookup = {
                str(s["brand_id"]): s.get("brand_name", "")
                for s in r.json().get("pool_sanitizers", [])
            }
        return self._sanitizer_lookup

    def fetch_water_test_data(self) -> dict[str, Any]:
        """Return the latest reading for every sensor."""
        try:
            home = self._fetch_home_dashboard()
            history = self._fetch_water_test_history()
            days_since = self._fetch_days_since_last_test()

            values: dict[str, Any] = {}

            latest_ts: str | None = None
            latest_results_id: str | None = None
            latest_is_store: bool | None = None
            for api_type, sensor_key, _name, _unit in CHEMISTRY_TESTS:
                latest = history.latest_for(api_type)
                values[sensor_key] = latest.value if latest else None
                if latest and (latest_ts is None or latest.timestamp > latest_ts):
                    latest_ts = latest.timestamp
                    latest_results_id = latest.results_id
                    latest_is_store = latest.is_store_test

            if latest_ts:
                values["test_date"] = _to_display_date(latest_ts)
                values["test_timestamp"] = _to_datetime(latest_ts)
                values["in_store"] = bool(latest_is_store)
                values["test_source"] = "In-Store" if latest_is_store else "AccuBlue Home"
                values["results_id"] = latest_results_id
            else:
                values["test_date"] = None
                values["test_timestamp"] = None
                values["in_store"] = None
                values["test_source"] = None
                values["results_id"] = None

            values["days_since_test"] = days_since
            values["sanitizer"] = home.sanitizer_name(self._get_sanitizer_lookup())
            values["pool_size"] = home.pool_size_gallons
            values["pool_name_sensor"] = home.pool_name

            self._last_successful_values = values
            return values
        except (requests.RequestException, LesliesPoolError, ValueError) as err:
            _LOGGER.error("Leslie's API fetch failed: %s", err)
            if self._last_successful_values:
                _LOGGER.info("Returning cached values from last successful fetch")
                return self._last_successful_values
            raise

    def _fetch_home_dashboard(self) -> _HomeData:
        r = self._session.get(
            f"{BOOMI_BASE_URL}/ws/rest/Mobile/RelateORCE/home/v4",
            headers=self._boomi_headers(),
            timeout=20,
        )
        r.raise_for_status()
        profiles = r.json().get("pool_profile") or []
        match = next((p for p in profiles if str(p.get("id")) == self._pool_profile_id), None)
        if match is None and profiles:
            match = profiles[0]
        if match is None:
            raise PoolNotFoundError("home/v4 returned no pool profiles")
        return _HomeData(match)

    def _fetch_water_test_history(self) -> _History:
        # Boomi expects "yyyyMMdd HHmmss.fff" (literal space, not ISO 8601).
        end = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y%m%d 235959.999")
        start = "20200101 000000.000"
        r = self._session.get(
            f"{BOOMI_BASE_URL}/ws/rest/Mobile/waterTesting/history/v2",
            headers=self._boomi_headers(),
            params={
                "pool_profile_id": self._pool_profile_id,
                "start_date": start,
                "end_date": end,
            },
            timeout=30,
        )
        r.raise_for_status()
        return _History(r.json().get("water_test_history", {}).get("water_tests") or [])

    def _fetch_days_since_last_test(self) -> int | None:
        try:
            r = self._session.get(
                f"{BOOMI_BASE_URL}/ws/rest/Mobile/waterTesting/DaysSinceWaterTest",
                headers=self._boomi_headers(),
                params={"pool_profile_id": self._pool_profile_id},
                timeout=15,
            )
            r.raise_for_status()
            return int(r.json().get("no_of_days_since_last_watertest"))
        except (requests.RequestException, ValueError, TypeError):
            return None


@dataclass(frozen=True)
class _Reading:
    value: Any
    timestamp: str
    is_store_test: bool
    results_id: str | None


class _History:
    """Latest-by-type lookup over the water_tests list."""

    def __init__(self, raw_tests: list[dict[str, Any]]) -> None:
        self._by_type: dict[str, list[_Reading]] = {}
        for t in raw_tests:
            readings = [
                _Reading(
                    value=v.get("value"),
                    timestamp=v.get("timestamp") or "",
                    is_store_test=bool(v.get("is_store_test")),
                    results_id=v.get("results_id"),
                )
                for v in (t.get("water_test_values") or [])
                if v.get("value") is not None and v.get("timestamp")
            ]
            self._by_type[t.get("water_test_type", "")] = readings

    def latest_for(self, api_type: str) -> _Reading | None:
        readings = self._by_type.get(api_type) or []
        if not readings:
            return None
        return max(readings, key=lambda r: r.timestamp)


class _HomeData:
    """Pool profile from the home/v4 response."""

    def __init__(self, raw: dict[str, Any]) -> None:
        self._raw = raw

    @property
    def pool_name(self) -> str | None:
        return self._raw.get("pool_name")

    @property
    def pool_size_gallons(self) -> int | None:
        size = self._raw.get("size_in_gallons")
        try:
            return int(size) if size is not None else None
        except (TypeError, ValueError):
            return None

    def sanitizer_name(self, lookup: dict[str, str]) -> str | None:
        code = self._raw.get("sanitization")
        if code is None:
            return None
        return lookup.get(str(code))


def _to_datetime(boomi_ts: str) -> datetime | None:
    try:
        return datetime.strptime(boomi_ts, "%Y%m%d %H%M%S.%f").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _to_display_date(boomi_ts: str) -> str | None:
    """Format the Boomi timestamp as MM/DD/YYYY (matches the v2 sensor format)."""
    dt = _to_datetime(boomi_ts)
    return dt.strftime("%m/%d/%Y") if dt else None
