"""Tests for configuration settings."""

import os
from contextlib import contextmanager

from config.settings import Chain, LLMProvider, Settings

# Environment variables that Settings reads; isolated so tests are
# deterministic regardless of the developer machine / CI environment.
_ENV_VARS = [
    "LLM_PROVIDER",
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_MODEL",
    "KEEPERHUB_API_KEY",
    "KEEPERHUB_MCP_URL",
    "KEEPERHUB_CHAIN",
    "WALLET_ADDRESS",
    "PORTFOLIO_REBALANCE_THRESHOLD",
    "LIQUIDATION_THRESHOLD",
    "LIQUIDATION_CRITICAL",
    "MONITOR_INTERVAL_SECONDS",
    "PORTFOLIO_TARGETS",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "DISCORD_WEBHOOK_URL",
    "MAX_TRANSACTION_USD",
    "AUTO_APPROVE_MAX_USD",
    "BLOCK_THRESHOLD_USD",
    "LOG_LEVEL",
    "LOG_FILE",
]


@contextmanager
def _isolated_env():
    """Temporarily remove DeFi Sentinel env vars from the process."""
    saved = {k: os.environ.get(k) for k in _ENV_VARS}
    for k in _ENV_VARS:
        os.environ.pop(k, None)
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _empty_settings(**kwargs) -> Settings:
    """Build Settings without loading local .env, so tests are deterministic."""
    return Settings(_env_file=None, **kwargs)


def test_default_settings():
    """Test default settings values."""
    with _isolated_env():
        settings = _empty_settings()
    assert settings.llm_provider == LLMProvider.OPENAI
    assert settings.keeperhub_chain == Chain.BASE_SEPOLIA
    assert settings.monitor_interval_seconds == 60
    assert settings.liquidation_threshold == 1.5
    assert settings.liquidation_critical == 1.2


def test_portfolio_targets_parsing():
    """Test portfolio targets string parsing."""
    with _isolated_env():
        settings = _empty_settings(portfolio_targets="0xETH:60;0xUSDC:40")
    targets = settings.parsed_portfolio_targets
    assert len(targets) == 2
    assert targets[0]["token_address"] == "0xETH"
    assert targets[0]["percentage"] == 60.0
    assert targets[1]["token_address"] == "0xUSDC"
    assert targets[1]["percentage"] == 40.0


def test_empty_portfolio_targets():
    """Test empty portfolio targets."""
    with _isolated_env():
        settings = _empty_settings(portfolio_targets="")
    assert settings.parsed_portfolio_targets == []


def test_notification_config_checks():
    """Test notification configuration checks."""
    with _isolated_env():
        settings = _empty_settings()
    assert not settings.is_telegram_configured()
    assert not settings.is_discord_configured()

    settings.telegram_bot_token = "token"
    settings.telegram_chat_id = "123"
    assert settings.is_telegram_configured()

    settings.discord_webhook_url = "https://discord.com/api/webhooks/test"
    assert settings.is_discord_configured()


def test_keeperhub_config_check():
    """Test KeeperHub configuration check."""
    with _isolated_env():
        settings = _empty_settings()
    assert not settings.is_keeperhub_configured()

    settings.keeperhub_api_key = "kh-test"
    assert settings.is_keeperhub_configured()


def test_llm_config_check():
    """Test LLM configuration check."""
    with _isolated_env():
        settings = _empty_settings(llm_provider=LLMProvider.OPENAI)
    assert not settings.is_llm_configured()

    settings.openai_api_key = "sk-test"
    assert settings.is_llm_configured()

    with _isolated_env():
        settings2 = _empty_settings(llm_provider=LLMProvider.ANTHROPIC)
    assert not settings2.is_llm_configured()

    settings2.anthropic_api_key = "sk-ant-test"
    assert settings2.is_llm_configured()
