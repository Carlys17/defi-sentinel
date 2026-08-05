"""Tests for configuration settings."""

import pytest
from pydantic import ValidationError

from config.settings import Settings, LLMProvider, Chain


def test_default_settings():
    """Test default settings values."""
    settings = Settings()
    assert settings.llm_provider == LLMProvider.OPENAI
    assert settings.keeperhub_chain == Chain.BASE_SEPOLIA
    assert settings.monitor_interval_seconds == 60
    assert settings.liquidation_threshold == 1.5
    assert settings.liquidation_critical == 1.2


def test_portfolio_targets_parsing():
    """Test portfolio targets string parsing."""
    settings = Settings(portfolio_targets="0xETH:60;0xUSDC:40")
    targets = settings.parsed_portfolio_targets
    assert len(targets) == 2
    assert targets[0]["token_address"] == "0xETH"
    assert targets[0]["percentage"] == 60.0
    assert targets[1]["token_address"] == "0xUSDC"
    assert targets[1]["percentage"] == 40.0


def test_empty_portfolio_targets():
    """Test empty portfolio targets."""
    settings = Settings(portfolio_targets="")
    assert settings.parsed_portfolio_targets == []


def test_notification_config_checks():
    """Test notification configuration checks."""
    settings = Settings()
    assert not settings.is_telegram_configured()
    assert not settings.is_discord_configured()

    settings.telegram_bot_token = "token"
    settings.telegram_chat_id = "123"
    assert settings.is_telegram_configured()

    settings.discord_webhook_url = "https://discord.com/api/webhooks/test"
    assert settings.is_discord_configured()


def test_keeperhub_config_check():
    """Test KeeperHub configuration check."""
    settings = Settings()
    assert not settings.is_keeperhub_configured()

    settings.keeperhub_api_key = "kh-test"
    assert settings.is_keeperhub_configured()


def test_llm_config_check():
    """Test LLM configuration check."""
    settings = Settings(llm_provider=LLMProvider.OPENAI)
    assert not settings.is_llm_configured()

    settings.openai_api_key = "sk-test"
    assert settings.is_llm_configured()

    settings2 = Settings(llm_provider=LLMProvider.ANTHROPIC)
    assert not settings2.is_llm_configured()

    settings2.anthropic_api_key = "sk-ant-test"
    assert settings2.is_llm_configured()