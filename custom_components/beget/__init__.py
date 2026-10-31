"""The Beget integration: account balance from the Beget hosting API."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BegetApi
from .coordinator import BegetCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

type BegetConfigEntry = ConfigEntry[BegetCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: BegetConfigEntry) -> bool:
    """Set up Beget from a config entry."""
    api = BegetApi(
        async_get_clientsession(hass),
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    coordinator = BegetCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BegetConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
