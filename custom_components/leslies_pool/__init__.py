"""Initialize Leslie's Pool Water Tests integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .api import LesliesPoolApi, LesliesPoolError
from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Leslie's Pool Water Tests from a config entry."""

    if entry.version < 2:
        if not await _migrate_v1_entry(hass, entry):
            return False

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


async def _migrate_v1_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Translate a v1 entry (URL-paste flow) to v2 (Boomi flow)."""
    old = entry.data
    email = old.get("username") or old.get("email")
    password = old.get("password")
    if not email or not password:
        _LOGGER.error("Cannot migrate Leslie's entry: missing email/password")
        return False
    try:
        customer_id, relate_id = await hass.async_add_executor_job(
            LesliesPoolApi.resolve_relate_customer_id, email, password
        )
    except LesliesPoolError as err:
        _LOGGER.error("Migration failed: %s. User must reconfigure the integration.", err)
        return False

    new_data = {
        "email": email,
        "password": password,
        "relate_customer_id": relate_id,
        "customer_id": customer_id,
        "pool_profile_id": old["pool_profile_id"],
        "pool_name": old.get("pool_name", "Pool"),
        "scan_interval": old.get("scan_interval", 300),
    }
    hass.config_entries.async_update_entry(
        entry,
        data=new_data,
        version=2,
        unique_id=f"leslies_{relate_id}",
    )
    _LOGGER.info("Migrated Leslie's Pool entry to v2 (relate_customer_id=%s)", relate_id)
    return True
