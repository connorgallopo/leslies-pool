"""Initialize Leslie's Pool Water Tests integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .api import InvalidAuthError, LesliesPoolApi, LesliesPoolError
from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Leslie's Pool Water Tests from a config entry."""
    data = entry.data

    # Entries migrated from v1 don't have the relateCustomerID yet. Look it up
    # now using the saved email/password, then persist it on the entry so we
    # don't have to do this every time.
    if not data.get("relate_customer_id"):
        try:
            customer_id, relate_id = await hass.async_add_executor_job(
                LesliesPoolApi.resolve_relate_customer_id,
                data["email"],
                data["password"],
            )
        except InvalidAuthError as err:
            raise ConfigEntryAuthFailed(
                "Leslie's rejected the saved email/password. Reconfigure the integration."
            ) from err
        except LesliesPoolError as err:
            raise ConfigEntryNotReady(f"Couldn't reach Leslie's API: {err}") from err

        hass.config_entries.async_update_entry(
            entry,
            data={**data, "customer_id": customer_id, "relate_customer_id": relate_id},
            unique_id=f"leslies_{relate_id}",
        )
        data = entry.data

    api = LesliesPoolApi(
        relate_customer_id=data["relate_customer_id"],
        email=data["email"],
        pool_profile_id=data["pool_profile_id"],
        pool_name=data["pool_name"],
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = api
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if DOMAIN in hass.data:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate v1 entries (URL-paste flow) to v2 (Boomi flow).

    Only renames `username` to `email`. The relateCustomerID lookup is
    deferred to async_setup_entry so transient network failures don't
    permanently brick the entry.
    """
    if entry.version == 1:
        old = entry.data
        new_data = dict(old)
        if "username" in new_data and "email" not in new_data:
            new_data["email"] = new_data.pop("username")
        new_data.setdefault("pool_name", "Pool")
        new_data.setdefault("scan_interval", 300)

        hass.config_entries.async_update_entry(entry, data=new_data, version=2)
        _LOGGER.info("Migrated Leslie's Pool entry to v2")

    return True
