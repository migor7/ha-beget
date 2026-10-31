"""Sensors for Beget."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfInformation, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import BegetConfigEntry
from .const import UNLIMITED
from .coordinator import BegetCoordinator
from .entity import BegetEntity

CURRENCY = "RUB"


def _num(value: Any) -> float | None:
    """Beget mixes numbers and numeric strings; normalise to float."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _limit(value: Any) -> float | None:
    num = _num(value)
    return None if num is None or num >= UNLIMITED else num


def _block_date(data: dict[str, Any]) -> date | None:
    days = _num(data.get("user_days_to_block"))
    if days is None:
        return None
    return dt_util.now().date() + timedelta(days=int(days))


def _disk_percent(data: dict[str, Any]) -> float | None:
    used = _num(data.get("user_quota"))
    total = _limit(data.get("plan_quota"))
    if used is None or not total:
        return None
    return round(used / total * 100, 1)


@dataclass(frozen=True, kw_only=True)
class BegetSensorDescription(SensorEntityDescription):
    """Describes a Beget sensor."""

    value_fn: Callable[[dict[str, Any]], Any]
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


SENSORS: tuple[BegetSensorDescription, ...] = (
    BegetSensorDescription(
        key="balance",
        translation_key="balance",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=CURRENCY,
        suggested_display_precision=2,
        value_fn=lambda d: _num(d.get("user_balance")),
    ),
    BegetSensorDescription(
        key="days_to_block",
        translation_key="days_to_block",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.DAYS,
        suggested_unit_of_measurement=UnitOfTime.DAYS,
        suggested_display_precision=0,
        value_fn=lambda d: _num(d.get("user_days_to_block")),
    ),
    BegetSensorDescription(
        key="block_date",
        translation_key="block_date",
        device_class=SensorDeviceClass.DATE,
        value_fn=_block_date,
    ),
    BegetSensorDescription(
        key="rate_day",
        translation_key="rate_day",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY,
        suggested_display_precision=2,
        value_fn=lambda d: _num(d.get("user_rate_current")),
    ),
    BegetSensorDescription(
        key="rate_month",
        translation_key="rate_month",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY,
        suggested_display_precision=0,
        value_fn=lambda d: _num(d.get("user_rate_month")),
    ),
    BegetSensorDescription(
        key="rate_year",
        translation_key="rate_year",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement=CURRENCY,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=lambda d: _num(d.get("user_rate_year")),
    ),
    BegetSensorDescription(
        key="plan",
        translation_key="plan",
        value_fn=lambda d: d.get("plan_name"),
        attrs_fn=lambda d: {
            "year_plan": str(d.get("user_is_year_plan")) == "1",
            "server": d.get("server_name"),
        },
    ),
    BegetSensorDescription(
        key="disk_used",
        translation_key="disk_used",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _num(d.get("user_quota")),
        attrs_fn=lambda d: {"quota_mb": _limit(d.get("plan_quota"))},
    ),
    BegetSensorDescription(
        key="disk_usage",
        translation_key="disk_usage",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_disk_percent,
    ),
    BegetSensorDescription(
        key="sites",
        translation_key="sites",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: _num(d.get("user_sites")),
        attrs_fn=lambda d: {"limit": _limit(d.get("plan_site"))},
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BegetConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Beget sensors."""
    coordinator = entry.runtime_data
    async_add_entities(BegetSensor(coordinator, desc) for desc in SENSORS)


class BegetSensor(BegetEntity, SensorEntity):
    """A Beget account sensor."""

    entity_description: BegetSensorDescription

    def __init__(
        self, coordinator: BegetCoordinator, description: BegetSensorDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator.data)
