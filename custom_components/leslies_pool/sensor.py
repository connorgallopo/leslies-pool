"""Sensor platform for Leslie's Pool Water Tests."""
import logging
from datetime import datetime, timedelta

import requests
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "free_chlorine": ("Leslie's Free Chlorine", "ppm"),
    "total_chlorine": ("Leslie's Total Chlorine", "ppm"),
    "ph": ("Leslie's pH", "pH"),
    "alkalinity": ("Leslie's Total Alkalinity", "ppm"),
    "calcium": ("Leslie's Calcium Hardness", "ppm"),
    "cyanuric_acid": ("Leslie's Cyanuric Acid", "ppm"),
    "iron": ("Leslie's Iron", "ppm"),
    "copper": ("Leslie's Copper", "ppm"),
    "phosphates": ("Leslie's Phosphates", "ppb"),
    "salt": ("Leslie's Salt", "ppm"),
    "last_tested": ("Leslie's Last Tested", None),  # New sensor for last tested
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Leslie's Pool Water Tests sensors from a config entry."""
    api = hass.data[DOMAIN][entry.entry_id]

    scan_interval = entry.data.get("scan_interval", 300)

    async def async_update_data():
        """Fetch data from API endpoint."""
        try:
            data = await hass.async_add_executor_job(api.fetch_water_test_data)
            data["last_tested"] = datetime.now().isoformat()  # Add timestamp
            return data
        except requests.RequestException as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="leslies_pool",
        update_method=async_update_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    await coordinator.async_refresh()

    sensors = [
        LesliesPoolSensor(coordinator, entry, sensor_type, name, unit)
        for sensor_type, (name, unit) in SENSOR_TYPES.items()
    ]

    async_add_entities(sensors, update_before_add=True)


class LesliesPoolSensor(SensorEntity):
    """Representation of a Leslie's Pool sensor."""

    def __init__(self, coordinator, config_entry, sensor_type, name, unit):
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self._sensor_type = sensor_type
        self._name = name
        self._unit = unit

    @property
    def unique_id(self):
        """Return a unique ID for this sensor."""
        return f"{self.config_entry.entry_id}_leslies_{self._sensor_type}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self._sensor_type)

    @property
    def available(self):
        """Return if the sensor is available."""
        return self.coordinator.last_update_success

    @property
    def device_info(self):
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            name="Leslie's Pool",
            manufacturer="Leslie's Pool",
            model="Water Test",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity."""
        return self._unit

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
