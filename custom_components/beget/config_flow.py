"""Config flow for Beget."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import BegetApi, BegetApiError, BegetAuthError, BegetConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PASSWORD_SELECTOR = TextSelector(
    TextSelectorConfig(type=TextSelectorType.PASSWORD, autocomplete="current-password")
)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT, autocomplete="username")
        ),
        vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR,
    }
)

REAUTH_SCHEMA = vol.Schema({vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR})


class BegetConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Beget."""

    VERSION = 1

    def __init__(self) -> None:
        self._api_error = ""

    async def _validate(self, login: str, password: str) -> dict[str, str]:
        api = BegetApi(async_get_clientsession(self.hass), login, password)
        try:
            await api.get_account_info()
        except BegetAuthError:
            return {"base": "invalid_auth"}
        except BegetConnectionError:
            return {"base": "cannot_connect"}
        except BegetApiError as err:
            self._api_error = str(err)
            return {"base": "api_error"}
        except Exception:
            _LOGGER.exception("Unexpected error while validating Beget credentials")
            return {"base": "unknown"}
        return {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for login and API password."""
        errors: dict[str, str] = {}
        if user_input is not None:
            login = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]
            await self.async_set_unique_id(login.lower())
            self._abort_if_unique_id_configured()

            errors = await self._validate(login, password)
            if not errors:
                return self.async_create_entry(
                    title=login,
                    data={CONF_USERNAME: login, CONF_PASSWORD: password},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                USER_SCHEMA,
                {CONF_USERNAME: user_input[CONF_USERNAME]} if user_input else {},
            ),
            errors=errors,
            description_placeholders={"error": self._api_error},
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start reauth when the API password stops working."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for a new API password."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = await self._validate(
                entry.data[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            if not errors:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=REAUTH_SCHEMA,
            errors=errors,
            description_placeholders={
                "username": entry.data[CONF_USERNAME],
                "error": self._api_error,
            },
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the API password from the integration menu (⋮ → Reconfigure)."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = await self._validate(
                entry.data[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            if not errors:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=REAUTH_SCHEMA,
            errors=errors,
            description_placeholders={
                "username": entry.data[CONF_USERNAME],
                "error": self._api_error,
            },
        )
