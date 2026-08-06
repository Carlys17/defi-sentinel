"""Discord notification provider for DeFi Sentinel."""

import logging
from typing import Optional

import httpx

from config.settings import Settings
from src.notifications.base import (
    Notification,
    NotificationLevel,
    NotificationProvider,
)

logger = logging.getLogger(__name__)


class DiscordProvider(NotificationProvider):
    """Send notifications via Discord Webhook."""

    EMBED_COLORS = {
        NotificationLevel.INFO: 0x0099FF,
        NotificationLevel.WARNING: 0xFF9900,
        NotificationLevel.CRITICAL: 0xFF0000,
    }

    def __init__(self, webhook_url: str):
        self._webhook_url = webhook_url
        self._client = httpx.AsyncClient(timeout=10.0)

    async def send(self, notification: Notification) -> bool:
        """Send a notification via Discord webhook."""
        try:
            color = self.EMBED_COLORS.get(notification.level, 0x0099FF)

            payload = {
                "embeds": [
                    {
                        "title": notification.title,
                        "description": notification.message[:1000],  # Discord limit
                        "color": color,
                        "footer": {"text": "DeFi Sentinel"},
                    }
                ]
            }

            if notification.metadata:
                fields = [
                    {
                        "name": k,
                        "value": str(v)[:100],
                        "inline": True,
                    }
                    for k, v in notification.metadata.items()
                ]
                payload["embeds"][0]["fields"] = fields

            response = await self._client.post(self._webhook_url, json=payload)
            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Discord send failed: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Discord send error: {e}")
            return False

    async def health_check(self) -> bool:
        """Check if Discord webhook is reachable."""
        try:
            response = await self._client.get(self._webhook_url)
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    @classmethod
    def from_settings(cls, settings: Settings) -> Optional["DiscordProvider"]:
        """Create provider from settings if configured."""
        if settings.is_discord_configured():
            return cls(settings.discord_webhook_url)
        return None
