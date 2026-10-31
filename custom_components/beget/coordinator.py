"""Data update coordinator for Beget."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BegetApi, BegetAuthError, BegetError
from .const import DOMAIN, RETRY_INTERVAL, UPDATE_INTERVAL

if TYPE_CHECKING:
    from . import BegetConfigEntry

_LOGGER = logging.getLogger(__name__)


class BegetCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetches account info once a day."""

    config_entry: BegetConfigEntry

    def __init__(self, hass: HomeAssistant, entry: BegetConfigEntry, api: BegetApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.api.get_account_info()
        except BegetAuthError as err:
            raise ConfigEntryAuthFailed(f"Beget authentication failed: {err}") from err
        except BegetError as err:
            # Не ждём сутки после сбоя — пробуем снова через RETRY_INTERVAL.
            self.update_interval = RETRY_INTERVAL
            raise UpdateFailed(f"Error fetching Beget account info: {err}") from err

        self.update_interval = UPDATE_INTERVAL
        return data
