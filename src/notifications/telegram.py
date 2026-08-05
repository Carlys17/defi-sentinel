"""Telegram notification provider for DeFi Sentinel."""

import logging
from typing import Optional

import httpx

from config.settings import Settings
from src.notifications.base import Notification, NotificationProvider

logger = logging.getLogger(__name__)


class TelegramProvider(NotificationProvider):
    """Send notifications via Telegram Bot API."""

    def __init__(self, bot_token: str, chat_id: str):
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._base_url = f"https://api.telegram.org/bot{bot_token}"
        self._client = httpx.AsyncClient(timeout=10.0)

    async def send(self, notification: Notification) -> bool:
        """Send a notification via Telegram."""
        try:
            response = await self._client.post(
                f"{self._base_url}/sendMessage",
                json={
                    "chat_id": self._chat_id,
                    "text": notification.format_html(),
                    "parse_mode": "HTML",
                },
            )
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            logger.error(f"Telegram send failed: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False

    async def health_check(self) -> bool:
        """Check if Telegram bot is reachable."""
        try:
            response = await self._client.get(f"{self._base_url}/getMe")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    @classmethod
    def from_settings(cls, settings: Settings) -> Optional["TelegramProvider"]:
        """Create provider from settings if configured."""
        if settings.is_telegram_configured():
            return cls(settings.telegram_bot_token, settings.telegram_chat_id)
        return None