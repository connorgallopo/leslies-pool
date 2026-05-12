"""Test the Leslie's Pool Water Tests sensors."""

import logging
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.leslies_pool.const import (
    CHEMISTRY_TESTS,
    DOMAIN,
    META_SENSORS,
)
from custom_components.leslies_pool.sensor import (
    LesliesPoolSensor,
    async_setup_entry,
)

_LOGGER = logging.getLogger(__name__)


MOCK_DATA = {
    "free_chlorine": 0.09,
    "total_chlorine": 0.34,
    "ph": 8.4,
    "alkalinity": 115,
    "calcium": 298,
    "cyanuric_acid": 39,
    "iron": 0.1,
    "copper": 0,
    "phosphates": 1962,
    "salt": 2637,
    "tds": 600,
    "bromine": None,
    "biguanides": None,
    "test_date": "05/09/2026",
    "in_store": True,
    "test_source": "In-Store",
    "days_since_test": 3,
    "results_id": "48255556",
    "sanitizer": "Salt 3000-4500",
    "pool_size": 30000,
    "pool_name_sensor": "Pool",
}


@pytest.fixture
def mock_coordinator(hass):
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="leslies_pool",
        update_method=AsyncMock(return_value=MOCK_DATA),
        update_interval=timedelta(seconds=300),
    )
    coordinator.data = MOCK_DATA
    coordinator.async_config_entry_first_refresh = AsyncMock()
    return coordinator


@pytest.fixture
def mock_entry():
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.data = {
        "email": "user@example.com",
        "password": "hunter2",
        "relate_customer_id": "15382105",
        "customer_id": "abc",
        "pool_profile_id": "5891278",
        "pool_name": "Backyard",
        "scan_interval": 300,
    }
    return entry


async def test_async_setup_entry_creates_all_sensors(hass, mock_entry, mock_coordinator):
    """async_setup_entry should create one sensor per CHEMISTRY_TESTS + META_SENSORS entry."""
    api = MagicMock()
    api.fetch_water_test_data = MagicMock(return_value=MOCK_DATA)
    hass.data = {DOMAIN: {mock_entry.entry_id: api}}

    add_entities = MagicMock()

    with patch(
        "custom_components.leslies_pool.sensor.DataUpdateCoordinator",
        return_value=mock_coordinator,
    ):
        await async_setup_entry(hass, mock_entry, add_entities)

    assert add_entities.call_count == 1
    created = add_entities.call_args[0][0]
    expected = len(CHEMISTRY_TESTS) + len(META_SENSORS)
    assert len(created) == expected


async def test_sensor_native_value(mock_entry, mock_coordinator):
    """native_value reads from coordinator.data by sensor_key."""
    sensor = LesliesPoolSensor(
        mock_coordinator, mock_entry, "free_chlorine", "Free Chlorine", "ppm"
    )
    assert sensor.native_value == 0.09
    assert sensor.native_unit_of_measurement == "ppm"
    assert sensor.unique_id == "test_entry_leslies_free_chlorine"
    assert sensor.has_entity_name is True
    assert sensor.name == "Free Chlorine"


async def test_sensor_attributes_include_test_metadata(mock_entry, mock_coordinator):
    """results_id, test_source, and test_timestamp surface as state attributes."""
    sensor = LesliesPoolSensor(
        mock_coordinator, mock_entry, "salt", "Salt", "ppm"
    )
    attrs = sensor.extra_state_attributes
    assert attrs["results_id"] == "48255556"
    assert attrs["test_source"] == "In-Store"


async def test_sensor_device_info(mock_entry, mock_coordinator):
    """Device name includes the configured pool name."""
    sensor = LesliesPoolSensor(
        mock_coordinator, mock_entry, "ph", "pH", "pH"
    )
    info = sensor.device_info
    assert info["name"] == "Leslie's Pool - Backyard"
    assert info["manufacturer"] == "Leslie's Pool Supplies"
