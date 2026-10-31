"""Base entity for Beget."""

from __future__ import annotations

from homeassistant.const import CONF_USERNAME
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONTROL_PANEL_URL, DOMAIN
from .coordinator import BegetCoordinator


class BegetEntity(CoordinatorEntity[BegetCoordinator]):
    """Common device info and unique id."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: BegetCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        login = entry.data[CONF_USERNAME]
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
            name=f"Beget {login}",
            manufacturer="Beget",
            model="Хостинг",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=CONTROL_PANEL_URL,
        )
