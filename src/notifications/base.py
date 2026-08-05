"""Base notification interface for DeFi Sentinel."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Notification:
    """A notification to be sent."""
    title: str
    message: str
    level: NotificationLevel = NotificationLevel.INFO
    metadata: Optional[dict] = None

    def format_text(self) -> str:
        """Format notification as plain text."""
        prefix = {
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.CRITICAL: "🚨",
        }.get(self.level, "📢")

        text = f"{prefix} **{self.title}**\n\n{self.message}"
        if self.metadata:
            text += "\n\n" + "\n".join(
                f"• {k}: {v}" for k, v in self.metadata.items()
            )
        return text

    def format_html(self) -> str:
        """Format notification as HTML (for Telegram)."""
        emoji = {
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.CRITICAL: "🚨",
        }.get(self.level, "📢")

        html = f"{emoji} <b>{self.title}</b>\n\n{self.message}"
        if self.metadata:
            html += "\n\n" + "\n".join(
                f"• <code>{k}</code>: {v}" for k, v in self.metadata.items()
            )
        return html


class NotificationProvider(ABC):
    """Abstract base class for notification providers."""

    @abstractmethod
    async def send(self, notification: Notification) -> bool:
        """Send a notification. Returns True if successful."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is reachable."""
        pass


class NotificationManager:
    """Manages multiple notification providers."""

    def __init__(self):
        self._providers: list[NotificationProvider] = []

    def add_provider(self, provider: NotificationProvider):
        """Add a notification provider."""
        self._providers.append(provider)
        logger.info(f"Added notification provider: {provider.__class__.__name__}")

    async def send(self, notification: Notification):
        """Send notification to all providers."""
        for provider in self._providers:
            try:
                success = await provider.send(notification)
                if success:
                    logger.debug(
                        f"Sent {notification.level.value} notification to "
                        f"{provider.__class__.__name__}"
                    )
                else:
                    logger.warning(
                        f"Failed to send notification to "
                        f"{provider.__class__.__name__}"
                    )
            except Exception as e:
                logger.error(
                    f"Error sending notification to "
                    f"{provider.__class__.__name__}: {e}"
                )

    async def send_alert(
        self,
        title: str,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        metadata: Optional[dict] = None,
    ):
        """Convenience method to send an alert."""
        notification = Notification(
            title=title,
            message=message,
            level=level,
            metadata=metadata,
        )
        await self.send(notification)