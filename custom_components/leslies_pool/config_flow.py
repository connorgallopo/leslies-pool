"""Config flow for Leslie's Pool Water Tests."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.exceptions import HomeAssistantError

from .api import (
    InvalidAuthError,
    LesliesPoolApi,
    LesliesPoolError,
    PoolNotFoundError,
    PoolProfile,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=300): vol.All(int, vol.Range(min=60)),
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the email/password + pool-picker setup flow."""

    VERSION = 2

    def __init__(self) -> None:
        self._email: str | None = None
        self._password: str | None = None
        self._scan_interval: int = 300
        self._relate_customer_id: str | None = None
        self._customer_id: str | None = None
        self._pools: list[PoolProfile] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Collect email + password, then resolve the user's pool list."""
        errors: dict[str, str] = {}
        if user_input is not None:
            email = user_input[CONF_EMAIL].strip()
            password = user_input[CONF_PASSWORD]
            scan_interval = user_input.get(CONF_SCAN_INTERVAL, 300)

            try:
                customer_id, relate_id = await self.hass.async_add_executor_job(
                    LesliesPoolApi.resolve_relate_customer_id, email, password
                )
                pools = await self.hass.async_add_executor_job(
                    LesliesPoolApi.discover_pool_profiles, email, relate_id
                )
            except InvalidAuthError:
                errors["base"] = "invalid_auth"
            except PoolNotFoundError:
                errors["base"] = "no_pools"
            except LesliesPoolError:
                _LOGGER.exception("Leslie's API error during setup")
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception during setup")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(f"leslies_{relate_id}")
                self._abort_if_unique_id_configured()

                self._email = email
                self._password = password
                self._scan_interval = scan_interval
                self._relate_customer_id = relate_id
                self._customer_id = customer_id
                self._pools = pools

                if len(pools) == 1:
                    return self._create_entry(pools[0])
                return await self.async_step_pick_pool()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_pick_pool(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Show the pool picker (only reached when account has 2+ pools)."""
        if user_input is not None:
            chosen = next(
                (p for p in self._pools if p.id == user_input["pool_profile_id"]),
                None,
            )
            if chosen is None:
                return self.async_abort(reason="pool_gone")
            return self._create_entry(chosen)

        pool_choices = {p.id: p.pool_name for p in self._pools}
        schema = vol.Schema({vol.Required("pool_profile_id"): vol.In(pool_choices)})
        return self.async_show_form(step_id="pick_pool", data_schema=schema)

    def _create_entry(self, pool: PoolProfile) -> config_entries.ConfigFlowResult:
        assert self._email and self._relate_customer_id
        return self.async_create_entry(
            title=f"Leslie's Pool - {pool.pool_name}",
            data={
                "email": self._email,
                "password": self._password,
                "relate_customer_id": self._relate_customer_id,
                "customer_id": self._customer_id,
                "pool_profile_id": pool.id,
                "pool_name": pool.pool_name,
                "scan_interval": self._scan_interval,
            },
        )


class CannotConnect(HomeAssistantError):
    """Leslie's API is unreachable."""


class InvalidAuth(HomeAssistantError):
    """Email or password rejected."""


class NoPools(HomeAssistantError):
    """Account has no registered pool profiles."""
