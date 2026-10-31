"""Constants for the Beget integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "beget"

API_BASE_URL: Final = "https://api.beget.com/api"
CONTROL_PANEL_URL: Final = "https://cp.beget.com"

# Данные обновляются раз в сутки, при ошибке — повтор через 30 минут.
UPDATE_INTERVAL: Final = timedelta(days=1)
RETRY_INTERVAL: Final = timedelta(minutes=30)

# Beget отдаёт это число вместо «без ограничений» в полях plan_*.
UNLIMITED: Final = 2147483647
