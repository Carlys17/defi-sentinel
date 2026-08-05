"""Tests for utility functions."""

import pytest

from src.utils.helpers import (
    format_ether,
    format_usd,
    format_percentage,
    safe_div,
    clamp,
    calculate_slippage,
)


def test_format_ether():
    """Test wei to ether conversion."""
    assert format_ether(1_000_000_000_000_000_000) == "1.000000"
    assert format_ether(1_500_000_000_000_000_000) == "1.500000"
    assert format_ether(0) == "0.000000"


def test_format_usd():
    """Test USD formatting."""
    assert format_usd(1000) == "$1,000.00"
    assert format_usd(1234.56) == "$1,234.56"
    assert format_usd(0) == "$0.00"


def test_format_percentage():
    """Test percentage formatting."""
    assert format_percentage(5.5) == "+5.50%"
    assert format_percentage(-2.3) == "-2.30%"
    assert format_percentage(0) == "+0.00%"


def test_safe_div():
    """Test safe division."""
    assert safe_div(10, 2) == 5.0
    assert safe_div(10, 0) == 0.0
    assert safe_div(10, 0, default=1.0) == 1.0


def test_clamp():
    """Test value clamping."""
    assert clamp(5, 0, 10) == 5
    assert clamp(-5, 0, 10) == 0
    assert clamp(15, 0, 10) == 10


def test_calculate_slippage():
    """Test slippage calculation."""
    assert calculate_slippage(100, 99, 0.01) is True
    assert calculate_slippage(100, 98, 0.01) is False
    assert calculate_slippage(0, 0) is True