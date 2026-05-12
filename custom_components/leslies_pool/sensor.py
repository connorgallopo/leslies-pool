"""Sensor platform for Leslie's Pool Water Tests."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import requests
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import LesliesPoolApi, LesliesPoolError
from .const import CHEMISTRY_TESTS, DOMAIN, META_SENSORS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Leslie's Pool sensors from a config entry."""
    api: LesliesPoolApi = hass.data[DOMAIN][entry.entry_id]
    scan_interval = int(entry.data.get("scan_interval", 300))

    async def async_update_data() -> dict[str, Any]:
        try:
            return await hass.async_add_executor_job(api.fetch_water_test_data)
        except (requests.RequestException, LesliesPoolError) as err:
            raise UpdateFailed(f"Error fetching Leslie's data: {err}") from err

    coordinator: DataUpdateCoordinator[dict[str, Any]] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="leslies_pool",
        update_method=async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_config_entry_first_refresh()

    # Pre-v3 entities used `{entry_id}_{sensor_key}` for the unique_id (no
    # `leslies_` segment). Migrate them so existing history sticks around.
    registry = er.async_get(hass)
    for sensor_key in (k for _api, k, _n, _u in CHEMISTRY_TESTS):
        new_uid = f"{entry.entry_id}_leslies_{sensor_key}"
        legacy_uid = f"{entry.entry_id}_{sensor_key}"
        if (eid := registry.async_get_entity_id("sensor", DOMAIN, legacy_uid)):
            registry.async_update_entity(eid, new_unique_id=new_uid)

    entities: list[SensorEntity] = []
    for _api_type, sensor_key, name, unit in CHEMISTRY_TESTS:
        entities.append(LesliesPoolSensor(coordinator, entry, sensor_key, name, unit))
    for sensor_key, name, unit in META_SENSORS:
        entities.append(LesliesPoolSensor(coordinator, entry, sensor_key, name, unit))

    async_add_entities(entities)


class LesliesPoolSensor(CoordinatorEntity[DataUpdateCoordinator[dict[str, Any]]], SensorEntity):
    """A single chemistry or meta sensor sourced from the coordinator."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[dict[str, Any]],
        entry: ConfigEntry,
        sensor_key: str,
        name: str,
        unit: str | None,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_key = sensor_key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_leslies_{sensor_key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Leslie's Pool - {entry.data.get('pool_name', 'Pool')}",
            manufacturer="Leslie's Pool Supplies",
            model="Water Test",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> Any:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._sensor_key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        attrs: dict[str, Any] = {}
        if (rid := data.get("results_id")) is not None:
            attrs["results_id"] = rid
        if (src := data.get("test_source")) is not None:
            attrs["test_source"] = src
        if (ts := data.get("test_timestamp")) is not None:
            attrs["test_timestamp"] = ts.isoformat() if isinstance(ts, datetime) else str(ts)
        return attrs
