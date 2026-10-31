"""Minimal async client for the Beget hosting API."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from .const import API_BASE_URL

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)

_AUTH_MARKERS = ("auth", "авториз", "парол", "password", "login", "логин")


class BegetError(Exception):
    """Base error for the Beget API."""


class BegetConnectionError(BegetError):
    """Beget API is unreachable or returned garbage."""


class BegetAuthError(BegetError):
    """Wrong login or API password, or API access is disabled."""


class BegetApiError(BegetError):
    """Beget API returned an error."""


class BegetApi:
    """Beget API client (https://beget.com/ru/kb/api)."""

    def __init__(self, session: aiohttp.ClientSession, login: str, password: str) -> None:
        self._session = session
        self._login = login
        self._password = password

    async def get_account_info(self) -> dict[str, Any]:
        """Return the result of user/getAccountInfo."""
        return await self._request("user/getAccountInfo")

    async def _request(self, method: str) -> dict[str, Any]:
        params = {
            "login": self._login,
            "passwd": self._password,
            "output_format": "json",
        }
        try:
            async with self._session.get(
                f"{API_BASE_URL}/{method}", params=params, timeout=REQUEST_TIMEOUT
            ) as resp:
                if resp.status >= 400:
                    # Не включаем URL в текст ошибки: в нём пароль.
                    raise BegetConnectionError(f"HTTP {resp.status}")
                payload = await resp.json(content_type=None)
        except BegetError:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
            raise BegetConnectionError(type(err).__name__) from None

        return _parse_payload(payload)


def _parse_payload(payload: Any) -> dict[str, Any]:
    """Unwrap {"status": ..., "answer": {"status": ..., "result": ...}}."""
    if not isinstance(payload, dict):
        raise BegetConnectionError("Unexpected response")

    if payload.get("status") != "success":
        code = str(payload.get("error_code") or "")
        text = str(payload.get("error_text") or code or "Unknown error")
        if code == "AUTH_ERROR" or any(m in text.lower() for m in _AUTH_MARKERS):
            raise BegetAuthError(text)
        raise BegetApiError(text)

    answer = payload.get("answer")
    if not isinstance(answer, dict):
        raise BegetConnectionError("Unexpected response")

    if answer.get("status") != "success":
        errors = answer.get("errors") or []
        texts = [
            str(e.get("error_text") or e.get("error_code"))
            for e in errors
            if isinstance(e, dict)
        ]
        raise BegetApiError("; ".join(texts) or "Unknown error")

    result = answer.get("result")
    if not isinstance(result, dict):
        raise BegetConnectionError("Unexpected response")
    return result
