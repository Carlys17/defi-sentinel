"""DeFi Sentinel - Main CLI entry point."""

import asyncio
import logging
import signal
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config.settings import Settings, get_settings
from src.agent.core import DeFiSentinelAgent, AgentState
from src.notifications.base import NotificationManager, NotificationLevel, LoggerProvider
from src.notifications.discord import DiscordProvider
from src.notifications.telegram import TelegramProvider
from src.observability.audit import AuditTrail, AuditEventType
from src.observability.metrics import MetricsCollector

app = typer.Typer(
    name="defi-sentinel",
    help="Autonomous AI Agent for DeFi Portfolio Management & Risk Protection",
    add_completion=False,
)
console = Console()


def setup_logging(settings: Settings):
    """Configure application logging."""
    log_dir = Path(settings.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, settings.log_level.value),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(settings.log_file, mode="a"),
        ],
    )


def create_notification_manager(settings: Settings) -> NotificationManager:
    """Create notification manager with configured providers."""
    manager = NotificationManager()

    # Always add logger provider
    manager.add_provider(LoggerProvider())

    # Add Telegram if configured
    if settings.is_telegram_configured():
        manager.add_provider(
            TelegramProvider(settings.telegram_bot_token, settings.telegram_chat_id)
        )

    # Add Discord if configured
    if settings.is_discord_configured():
        manager.add_provider(DiscordProvider(settings.discord_webhook_url))

    return manager


@app.command()
def start(
    interval: int = typer.Option(
        None, "--interval", "-i", help="Monitoring interval in seconds"
    ),
):
    """Start the DeFi Sentinel agent."""
    settings = get_settings()
    setup_logging(settings)
    logger = logging.getLogger(__name__)

    if interval:
        settings.monitor_interval_seconds = interval

    console.print(
        Panel(
            "[bold green]DeFi Sentinel[/bold green]\n"
            "[dim]Autonomous AI Agent for DeFi Portfolio Management[/dim]",
            title="🛡️",
            border_style="green",
        )
    )

    # Create components
    agent = DeFiSentinelAgent(settings)
    notification_mgr = create_notification_manager(settings)
    audit_trail = AuditTrail()
    metrics = MetricsCollector()

    # Initialize
    async def run():
        try:
            await agent.initialize()

            audit_trail.log(
                AuditEventType.AGENT_STARTED,
                "main",
                {
                    "strategies": list(agent._strategies.keys()),
                    "monitoring_interval": settings.monitor_interval_seconds,
                },
            )

            await notification_mgr.send_alert(
                "DeFi Sentinel Started",
                f"Agent initialized with {len(agent._strategies)} strategies",
                NotificationLevel.INFO,
            )

            # Start monitoring loop
            await agent.run_monitoring_loop()

        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            audit_trail.log(
                AuditEventType.AGENT_ERROR,
                "main",
                {"error": str(e)},
            )
        finally:
            await agent.stop()

            audit_trail.log(
                AuditEventType.AGENT_STOPPED,
                "main",
                {"summary": audit_trail.get_summary()},
            )

    asyncio.run(run())


@app.command()
def status():
    """Show agent status and configuration."""
    settings = get_settings()

    table = Table(title="DeFi Sentinel Status")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("LLM Provider", settings.llm_provider.value)
    table.add_row("KeeperHub Chain", settings.keeperhub_chain.value)
    table.add_row("Monitor Interval", f"{settings.monitor_interval_seconds}s")
    table.add_row("Liquidation Threshold", str(settings.liquidation_threshold))
    table.add_row("Rebalance Threshold", f"{settings.portfolio_rebalance_threshold}%")
    table.add_row("Max Transaction", f"${settings.max_transaction_usd:,.2f}")
    table.add_row("Telegram Configured", "✅" if settings.is_telegram_configured() else "❌")
    table.add_row("Discord Configured", "✅" if settings.is_discord_configured() else "❌")
    table.add_row("KeeperHub Configured", "✅" if settings.is_keeperhub_configured() else "❌")
    table.add_row("LLM Configured", "✅" if settings.is_llm_configured() else "❌")

    console.print(table)


@app.command()
def check():
    """Run health checks on all components."""
    settings = get_settings()
    setup_logging(settings)

    console.print("[bold]Running health checks...[/bold]\n")

    results = []

    # Check LLM
    if settings.is_llm_configured():
        results.append(("LLM", "✅ Configured", settings.llm_provider.value))
    else:
        results.append(("LLM", "❌ Not configured", ""))

    # Check KeeperHub
    if settings.is_keeperhub_configured():
        results.append(("KeeperHub", "✅ Configured", settings.keeperhub_chain.value))
    else:
        results.append(("KeeperHub", "❌ Not configured", ""))

    # Check Wallet
    if settings.wallet_address:
        results.append(("Wallet", "✅ Configured", settings.wallet_address[:10] + "..."))
    else:
        results.append(("Wallet", "❌ Not configured", ""))

    # Display results
    table = Table()
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Details", style="dim")

    for component, status, details in results:
        table.add_row(component, status, details)

    console.print(table)


def main():
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()