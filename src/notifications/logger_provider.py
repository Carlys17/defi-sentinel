"""Logger notification provider for DeFi Sentinel.

Sends notifications to the application logger as a fallback.
"""

import logging

from src.notifications.base import Notification, NotificationProvider

logger = logging.getLogger(__name__)


class LoggerProvider(NotificationProvider):
    """Send notifications to the application logger."""

    async def send(self, notification: Notification) -> bool:
        """Log the notification."""
        level_map = {
            "info": logger.info,
            "warning": logger.warning,
            "critical": logger.critical,
        }
        log_func = level_map.get(notification.level.value, logger.info)
        log_func(f"NOTIFICATION: {notification.format_text()}")
        return True

    async def health_check(self) -> bool:
        """Logger is always available."""
        return True
