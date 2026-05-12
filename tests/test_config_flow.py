"""Test the Leslie's Pool Water Tests config flow."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.leslies_pool.api import (
    InvalidAuthError,
    LesliesPoolError,
    PoolNotFoundError,
    PoolProfile,
)
from custom_components.leslies_pool.const import DOMAIN

USER_INPUT = {
    CONF_EMAIL: "user@example.com",
    CONF_PASSWORD: "hunter2",
    CONF_SCAN_INTERVAL: 300,
}

CUSTOMER_ID = "abonLs514W2HGuADKguRm0bs2F"
RELATE_ID = "15382105"

ONE_POOL = [PoolProfile(id="5891278", pool_name="Backyard")]
TWO_POOLS = [
    PoolProfile(id="5891278", pool_name="Backyard"),
    PoolProfile(id="5891279", pool_name="Spa"),
]


async def test_form(hass: HomeAssistant) -> None:
    """Test the user step renders the email/password form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_single_pool_creates_entry(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Account with one pool skips the picker and creates the entry."""
    with patch(
        "custom_components.leslies_pool.config_flow.LesliesPoolApi.resolve_relate_customer_id",
        return_value=(CUSTOMER_ID, RELATE_ID),
    ), patch(
        "custom_components.leslies_pool.config_flow.LesliesPoolApi.discover_pool_profiles",
        return_value=ONE_POOL,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Leslie's Pool - Backyard"
    assert result["data"]["email"] == "user@example.com"
    assert result["data"]["relate_customer_id"] == RELATE_ID
    assert result["data"]["pool_profile_id"] == "5891278"
    assert result["data"]["pool_name"] == "Backyard"
    assert result["data"]["scan_interval"] == 300


async def test_multiple_pools_shows_picker(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Account with multiple pools advances to the picker step."""
    with patch(
        "custom_components.leslies_pool.config_flow.LesliesPoolApi.resolve_relate_customer_id",
        return_value=(CUSTOMER_ID, RELATE_ID),
    ), patch(
        "custom_components.leslies_pool.config_flow.LesliesPoolApi.discover_pool_profiles",
        return_value=TWO_POOLS,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "pick_pool"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"pool_profile_id": "5891279"}
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Leslie's Pool - Spa"
    assert result["data"]["pool_profile_id"] == "5891279"
    assert result["data"]["pool_name"] == "Spa"


@pytest.mark.parametrize(
    ("exc", "expected_error"),
    [
        (InvalidAuthError("nope"), "invalid_auth"),
        (PoolNotFoundError("no pools"), "no_pools"),
        (LesliesPoolError("boom"), "cannot_connect"),
    ],
)
async def test_user_step_errors(
    hass: HomeAssistant, exc: Exception, expected_error: str
) -> None:
    """Surface API errors as form errors on the user step."""
    with patch(
        "custom_components.leslies_pool.config_flow.LesliesPoolApi.resolve_relate_customer_id",
        side_effect=exc,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": expected_error}
