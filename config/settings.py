"""Application settings using Pydantic Settings."""

from enum import StrEnum
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class Chain(StrEnum):
    ETHEREUM_SEPOLIA = "ethereum_sepolia"
    BASE_SEPOLIA = "base_sepolia"
    ARBITRUM_SEPOLIA = "arbitrum_sepolia"
    POLYGON_MUMBAI = "polygon_mumbai"
    BASE_MAINNET = "base_mainnet"
    ARBITRUM_MAINNET = "arbitrum_mainnet"
    ETHEREUM_MAINNET = "ethereum_mainnet"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class PortfolioTarget(BaseSettings):
    """Single portfolio allocation target."""

    token_address: str
    percentage: float

    @field_validator("percentage")
    @classmethod
    def validate_percentage(cls, v: float) -> float:
        if v < 0 or v > 100:
            raise ValueError("Percentage must be between 0 and 100")
        return v


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- LLM ---
    llm_provider: LLMProvider = LLMProvider.OPENAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # --- KeeperHub ---
    keeperhub_api_key: str = ""
    keeperhub_mcp_url: str = "https://app.keeperhub.com/mcp"
    keeperhub_chain: Chain = Chain.BASE_SEPOLIA

    # --- Wallet ---
    # Uses KeeperHub Turnkey wallet (server-side custody) — no private key needed
    wallet_address: str = ""

    # --- Portfolio ---
    portfolio_rebalance_threshold: float = 5.0
    liquidation_threshold: float = 1.5
    liquidation_critical: float = 1.2
    monitor_interval_seconds: int = 60
    portfolio_targets: str = ""

    # --- Notifications ---
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    discord_webhook_url: str = ""

    # --- Safety ---
    max_transaction_usd: float = 1000.0
    auto_approve_max_usd: float = 100.0
    block_threshold_usd: float = 5000.0

    # --- Logging ---
    log_level: LogLevel = LogLevel.INFO
    log_file: str = "logs/sentinel.log"

    @property
    def parsed_portfolio_targets(self) -> list[dict[str, str | float]]:
        """Parse portfolio targets string into list of dicts."""
        if not self.portfolio_targets:
            return []
        targets = []
        for item in self.portfolio_targets.split(";"):
            parts = item.strip().split(":")
            if len(parts) == 2:
                targets.append(
                    {
                        "token_address": parts[0].strip(),
                        "percentage": float(parts[1].strip()),
                    }
                )
        return targets

    def is_telegram_configured(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    def is_discord_configured(self) -> bool:
        return bool(self.discord_webhook_url)

    def is_keeperhub_configured(self) -> bool:
        return bool(self.keeperhub_api_key)

    def is_llm_configured(self) -> bool:
        if self.llm_provider == LLMProvider.OPENAI:
            return bool(self.openai_api_key)
        return bool(self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
