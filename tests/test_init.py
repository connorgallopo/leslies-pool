"""Test entry setup, migration, and unload."""

from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.leslies_pool.api import (
    InvalidAuthError,
    LesliesPoolError,
)
from custom_components.leslies_pool.const import DOMAIN


def _v1_entry() -> MockConfigEntry:
    """A v1 entry as produced by the old URL-paste config flow."""
    return MockConfigEntry(
        domain=DOMAIN,
        version=1,
        data={
            "title": "Leslie's Pool",
            "username": "user@example.com",
            "password": "hunter2",
            "pool_profile_id": "5891278",
            "pool_name": "Pool",
            "scan_interval": 300,
        },
        unique_id="legacy",
    )


def _v2_entry() -> MockConfigEntry:
    """A v2 entry as produced by the new config flow."""
    return MockConfigEntry(
        domain=DOMAIN,
        version=2,
        data={
            "email": "user@example.com",
            "password": "hunter2",
            "relate_customer_id": "15382105",
            "customer_id": "abc",
            "pool_profile_id": "5891278",
            "pool_name": "Pool",
            "scan_interval": 300,
        },
        unique_id="leslies_15382105",
    )


async def test_v1_entry_migrates_and_loads(hass: HomeAssistant):
    """v1 entries get username->email renamed and resolve relateCustomerID on first load."""
    entry = _v1_entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.leslies_pool.LesliesPoolApi.resolve_relate_customer_id",
        return_value=("abc", "15382105"),
    ), patch(
        "custom_components.leslies_pool.LesliesPoolApi.fetch_water_test_data",
        return_value={},
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.version == 2
    assert entry.data["email"] == "user@example.com"
    assert "username" not in entry.data
    assert entry.data["relate_customer_id"] == "15382105"
    assert entry.data["customer_id"] == "abc"


async def test_v2_entry_loads_without_relookup(hass: HomeAssistant):
    """A fully-formed v2 entry should not hit OCAPI again."""
    entry = _v2_entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.leslies_pool.LesliesPoolApi.resolve_relate_customer_id"
    ) as mock_resolve, patch(
        "custom_components.leslies_pool.LesliesPoolApi.fetch_water_test_data",
        return_value={},
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    mock_resolve.assert_not_called()


async def test_bad_password_triggers_auth_failed(hass: HomeAssistant):
    """If OCAPI rejects the credentials, setup raises ConfigEntryAuthFailed."""
    entry = _v1_entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.leslies_pool.LesliesPoolApi.resolve_relate_customer_id",
        side_effect=InvalidAuthError("nope"),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR


async def test_network_blip_triggers_retry(hass: HomeAssistant):
    """Transient API errors should put the entry in retry state, not auth-failed."""
    entry = _v1_entry()
    entry.add_to_hass(hass)

    with patch(
        "custom_components.leslies_pool.LesliesPoolApi.resolve_relate_customer_id",
        side_effect=LesliesPoolError("boom"),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY
