"""Manual refresh button for Beget."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BegetConfigEntry
from .entity import BegetEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BegetConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the refresh button."""
    async_add_entities([BegetRefreshButton(entry.runtime_data, "refresh")])


class BegetRefreshButton(BegetEntity, ButtonEntity):
    """Fetch account info now instead of waiting for the daily update."""

    _attr_translation_key = "refresh"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_press(self) -> None:
        await self.coordinator.async_request_refresh()
