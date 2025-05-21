"""Sensor platform for Leslie's Pool Water Tests."""

import logging
from datetime import datetime, timedelta

def parse_test_date(date_str):
    """Parse the test date string from Leslie's website into a datetime object."""
    if not date_str:
        return None
    
    try:
        # Parse MM/DD/YYYY format
        date_obj = datetime.strptime(date_str, "%m/%d/%Y")
        
        # Since we don't have a time component, set it to noon UTC to avoid timezone issues
        date_obj = date_obj.replace(hour=12, minute=0, second=0, microsecond=0)
        
        return date_obj
    except ValueError:
        _LOGGER.error(f"Failed to parse test date: {date_str}")
        return None

import requests
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "free_chlorine": ("Leslies Free Chlorine", "ppm"),
    "total_chlorine": ("Leslies Total Chlorine", "ppm"),
    "ph": ("Leslies pH", "pH"),
    "alkalinity": ("Leslies Total Alkalinity", "ppm"),
    "calcium": ("Leslies Calcium Hardness", "ppm"),
    "cyanuric_acid": ("Leslies Cyanuric Acid", "ppm"),
    "iron": ("Leslies Iron", "ppm"),
    "copper": ("Leslies Copper", "ppm"),
    "phosphates": ("Leslies Phosphates", "ppb"),
    "salt": ("Leslies Salt", "ppm"),
    "test_date": ("Leslies Last Tested", None),
    "in_store": ("Leslies In Store", None),
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
            # Ensure 'test_date' is included in the data
            if "test_date" in data:
                data["last_tested"] = data["test_date"]  # Use the 'test_date' value
                # Parse test_date into a datetime object
                data["test_timestamp"] = parse_test_date(data["test_date"])
            else:
                data["last_tested"] = None  # Fallback if 'test_date' is missing
                data["test_timestamp"] = None
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

    # Access the entity registry
    entity_registry = er.async_get(hass)

    sensors = []
    for sensor_type, (name, unit) in SENSOR_TYPES.items():
        unique_id = f"{entry.entry_id}_leslies_{sensor_type}"

        # Try to find the entity in the registry using the unique ID
        entity_id = entity_registry.async_get_entity_id("sensor", DOMAIN, unique_id)

        # If the entity is not found, check for the old format without "leslies_"
        if not entity_id:
            old_unique_id = f"{entry.entry_id}_{sensor_type}"  # Old unique ID format
            entity_id = entity_registry.async_get_entity_id(
                "sensor", DOMAIN, old_unique_id
            )

            # If an old entity is found, update its unique ID and entity_id
            if entity_id:
                new_entity_id = f"sensor.leslies_{sensor_type}"
                entity_registry.async_update_entity(entity_id, new_unique_id=unique_id)
                entity_registry.async_update_entity(
                    entity_id, new_entity_id=new_entity_id
                )

        # Create the sensor entity
        sensors.append(LesliesPoolSensor(coordinator, entry, sensor_type, name, unit))

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
        self._attr_last_updated = None

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
        
    @property
    def last_updated(self):
        """Return the timestamp of when the sensor state was last updated."""
        if self.coordinator.data and "test_timestamp" in self.coordinator.data:
            return self.coordinator.data.get("test_timestamp")
        
        # Fall back to the default behavior if no test timestamp is available
        return super().last_updated
