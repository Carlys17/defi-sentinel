"""Utility functions for DeFi Sentinel."""

import logging
import time
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def format_ether(wei: int | float, decimals: int = 18) -> str:
    """Convert wei to ether string."""
    return f"{float(wei) / (10 ** decimals):.6f}"


def format_usd(amount: float) -> str:
    """Format USD amount."""
    return f"${amount:,.2f}"


def format_percentage(value: float) -> str:
    """Format percentage with sign."""
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"


def timestamp_to_iso(ts: float) -> str:
    """Convert unix timestamp to ISO 8601 string."""
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def now_iso() -> str:
    """Get current time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def now_ts() -> float:
    """Get current unix timestamp."""
    return time.time()


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default on zero."""
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(value, max_val))


def calculate_slippage(
    expected: float, actual: float, tolerance: float = 0.01
) -> bool:
    """Check if slippage is within tolerance.

    Returns True if slippage is acceptable.
    """
    if expected == 0:
        return actual == 0
    slippage = abs(expected - actual) / expected
    return slippage <= tolerance


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential: bool = True,
):
    """Decorator for retrying async functions with exponential backoff.

    Usage:
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        async def my_function():
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"Function '{func.__name__}' failed after {max_retries} attempts"
                        )
                        raise
                    delay = min(
                        base_delay * (2 ** attempt if exponential else attempt),
                        max_delay,
                    )
                    logger.warning(
                        f"Retry {attempt}/{max_retries} for '{func.__name__}' "
                        f"in {delay}s: {e}"
                    )
                    import asyncio
                    await asyncio.sleep(delay)
            raise last_exception  # type: ignore
        return wrapper
    return decorator