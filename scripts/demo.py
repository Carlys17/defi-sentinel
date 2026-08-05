#!/usr/bin/env python3
"""
DeFi Sentinel — Hackathon Demo Script
======================================

Simulates the full autonomous agent lifecycle with realistic, fake data.
Designed to be screen-recorded as a demo video for the hackathon submission.

This script mirrors the real agent flow defined in src/agent/core.py:
  1. Initialization (config, KeeperHub, LLM, strategies)
  2. Portfolio scan (Aave V3 + Compound V3 positions)
  3. Liquidation shield detection (health factor warning)
  4. LLM reasoning step (structured JSON decision output)
  5. KeeperHub simulation (gas estimate + revert check)
  6. KeeperHub execution (on-chain transaction confirmation)
  7. Yield optimizer (cross-protocol APR comparison)
  8. Portfolio rebalance (target allocation enforcement)
  9. Notifications (Telegram + Discord)
  10. Audit trail summary
  11. Final dashboard

Usage:
    python scripts/demo.py          # Full demo (~75s)
    python scripts/demo.py --fast   # Quick preview (~30s)

Runtime: ~75 seconds (configurable via --fast for quick previews)
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Try to use rich; fall back to raw ANSI codes
# ---------------------------------------------------------------------------
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.syntax import Syntax
    from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
    from rich.columns import Columns
    from rich import box

    USE_RICH = True
    console = Console()
except ImportError:
    USE_RICH = False
    console = None  # type: ignore


# ---------------------------------------------------------------------------
# ANSI helpers (used when rich is unavailable)
# ---------------------------------------------------------------------------
class _ANSI:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def _p(text: str = "", end: str = "\n", bold: bool = False, color: str = ""):
    """Print with optional ANSI styling (rich fallback)."""
    if USE_RICH:
        console.print(text, end=end)
        return
    parts = []
    if bold:
        parts.append(_ANSI.BOLD)
    if color:
        parts.append(getattr(_ANSI, color.upper(), ""))
    parts.append(text)
    parts.append(_ANSI.RESET)
    sys.stdout.write("".join(parts) + end)
    sys.stdout.flush()


def _sep(char: str = "═", width: int = 70, color: str = "CYAN"):
    if USE_RICH:
        console.print(char * width, style=f"bold {color.lower()}")
    else:
        _p(char * width, color=color)


def _hdr(title: str, subtitle: str = ""):
    if USE_RICH:
        console.print()
        console.print(f"[bold cyan]{title}[/bold cyan]", justify="center")
        if subtitle:
            console.print(f"[dim]{subtitle}[/dim]", justify="center")
        console.print()
    else:
        print()
        _p(title, bold=True, color="CYAN")
        if subtitle:
            _p(subtitle, color="DIM")
        print()


def _sleep(secs: float, fast: bool = False):
    """Sleep with optional fast-forward for quick previews."""
    if fast:
        time.sleep(min(secs, 0.3))
    else:
        time.sleep(secs)


# ---------------------------------------------------------------------------
# ASCII Art
# ---------------------------------------------------------------------------
ASCII_LOGO = r"""
  ██████╗ ██████╗  █████╗  ██████╗██╗  ██╗███████╗██████╗
  ██╔══██╗██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
  ██████╔╝██████╔╝███████║██║     █████╔╝ █████╗  ██████╔╝
  ██╔═══╝ ██╔══██╗██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
  ██║     ██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║
  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
"""

ASCII_SUBTITLE = r"""
  ╔══════════════════════════════════════════════════════════╗
  ║   Autonomous AI Agent for DeFi Portfolio Management      ║
  ║   Risk Protection · Yield Optimization · Auto-Rebalance  ║
  ╚══════════════════════════════════════════════════════════╝
"""


def print_logo():
    if USE_RICH:
        console.print()
        console.print(ASCII_LOGO, style="bold cyan", justify="center")
        console.print()
        console.print(ASCII_SUBTITLE, style="bold green", justify="center")
        console.print()
    else:
        print()
        _p(ASCII_LOGO, color="CYAN")
        print()
        _p(ASCII_SUBTITLE, color="GREEN")
        print()


# ---------------------------------------------------------------------------
# Realistic fake data — aligned with actual src/ models
# ---------------------------------------------------------------------------

# Matches PortfolioState.positions shape from src/agent/core.py
PORTFOLIO_POSITIONS = [
    {
        "protocol": "Aave V3",
        "asset": "WETH",
        "action": "Supplied",
        "amount": "12.4500",
        "value_usd": 42_345.00,
        "apy": "2.34%",
        "health_factor": 2.87,
    },
    {
        "protocol": "Aave V3",
        "asset": "USDC",
        "action": "Borrowed",
        "amount": "15,000.00",
        "value_usd": 15_000.00,
        "apy": "4.12%",
        "health_factor": 2.87,
    },
    {
        "protocol": "Compound V3",
        "asset": "USDC",
        "action": "Supplied",
        "amount": "28,500.00",
        "value_usd": 28_500.00,
        "apy": "4.87%",
        "health_factor": "N/A",
    },
    {
        "protocol": "Aave V3",
        "asset": "WBTC",
        "action": "Supplied",
        "amount": "0.8500",
        "value_usd": 58_920.00,
        "apy": "0.89%",
        "health_factor": 2.87,
    },
    {
        "protocol": "Compound V3",
        "asset": "WETH",
        "action": "Borrowed",
        "amount": "3.2000",
        "value_usd": 10_933.33,
        "apy": "3.56%",
        "health_factor": "N/A",
    },
    {
        "protocol": "Aave V3",
        "asset": "stETH",
        "action": "Supplied",
        "amount": "5.6000",
        "value_usd": 19_152.00,
        "apy": "3.12%",
        "health_factor": 2.87,
    },
]

YIELD_OPPORTUNITIES = [
    {
        "current_protocol": "Compound V3",
        "asset": "USDC",
        "current_apy": "4.87%",
        "better_protocol": "Aave V3",
        "better_apy": "5.42%",
        "improvement": "+0.55%",
        "est_annual_gain": "$156.75",
        "gas_cost": "$4.20",
        "net_gain": "$152.55",
    },
    {
        "current_protocol": "Aave V3",
        "asset": "WBTC",
        "current_apy": "0.89%",
        "better_protocol": "Morpho",
        "better_apy": "1.47%",
        "improvement": "+0.58%",
        "est_annual_gain": "$341.74",
        "gas_cost": "$6.80",
        "net_gain": "$334.94",
    },
]

LLM_REASONING_STEPS = [
    ("Analyzing portfolio composition", "Scanning 6 positions across 2 protocols..."),
    ("Risk assessment", "Health factor 2.87 — well above liquidation threshold (1.50)"),
    ("Market context", "ETH -3.2% in 24h, BTC +0.8%. Volatility elevated."),
    ("Strategy evaluation", "LiquidationShield: SAFE | YieldOptimizer: OPPORTUNITY | Rebalancer: TRIGGERED"),
    ("Decision synthesis", "3 actions identified: repay, supply, rebalance"),
    ("Gas estimation", "Total estimated gas: ~$18.40 across 3 txns"),
    ("Final verdict", "Net positive impact: +$514.24/year. Proceeding."),
]

# Matches AuditEventType values from src/observability/audit.py
AUDIT_ENTRIES = [
    {"ts": "2025-07-12T14:32:01Z", "event": "agent_started", "detail": "3 strategies loaded, LLM=gpt-4o-mini", "status": "OK"},
    {"ts": "2025-07-12T14:32:03Z", "event": "portfolio_snapshot", "detail": "6 positions, 2 protocols, $174,850.33", "status": "OK"},
    {"ts": "2025-07-12T14:32:05Z", "event": "liquidation_risk", "detail": "HF=1.52 approaching threshold 1.50 — CRITICAL", "status": "WARN"},
    {"ts": "2025-07-12T14:32:08Z", "event": "decision_made", "detail": "3 decisions: repay_debt(p1), yield_opt(p2), rebalance(p3)", "status": "DONE"},
    {"ts": "2025-07-12T14:32:10Z", "event": "transaction_sent", "detail": "3 txns submitted via KeeperHub (gas=$18.40)", "status": "SENT"},
    {"ts": "2025-07-12T14:32:13Z", "event": "transaction_confirmed", "detail": "All 3 txns confirmed in blocks 21048372-374", "status": "OK"},
    {"ts": "2025-07-12T14:32:15Z", "event": "yield_opportunity", "detail": "USDC: 4.87%→5.42% (+$152.55/yr), WBTC: 0.89%→1.47% (+$334.94/yr)", "status": "DONE"},
    {"ts": "2025-07-12T14:32:17Z", "event": "portfolio_rebalanced", "detail": "Debt ratio 32.4% → 30.0% (target)", "status": "DONE"},
    {"ts": "2025-07-12T14:32:19Z", "event": "alert_triggered", "detail": "Telegram + Discord notifications dispatched", "status": "SENT"},
]


# ---------------------------------------------------------------------------
# Demo steps — each mirrors a real agent lifecycle phase
# ---------------------------------------------------------------------------

def step_initialization(fast: bool):
    """Step 1: Agent initialization — mirrors DeFiSentinelAgent.initialize()"""
    _hdr("STEP 1 / 9  —  INITIALIZATION", "Loading config, connecting to KeeperHub, LLM ready")
    _sep()
    _sleep(0.5, fast)

    lines = [
        "[bold green]✓[/bold green] Config loaded from .env (chain=ethereum-mainnet)",
        "[bold green]✓[/bold green] LLM provider: [bold]OpenAI gpt-4o-mini[/bold] (temperature=0.1)",
        "[bold green]✓[/bold green] KeeperHub connected: [bold]wss://mainnet.keeperhub.network/v1[/bold]",
        "[bold green]✓[/bold green] Wallet: [bold]0x742d...8f3a[/bold] (balance: 2.45 ETH)",
        "[bold green]✓[/bold green] Strategies loaded: [bold]LiquidationShield[/bold], [bold]YieldOptimizer[/bold], [bold]PortfolioRebalancer[/bold]",
        "[bold green]✓[/bold green] Notifications: [bold]Telegram[/bold] (Bot ID: 7891234567), [bold]Discord[/bold] (Webhook configured)",
        "[bold green]✓[/bold green] Audit logger initialized → [dim]logs/audit.jsonl[/dim]",
    ]

    if USE_RICH:
        for line in lines:
            console.print(f"  {line}")
            _sleep(0.15, fast)
    else:
        for line in lines:
            _p(f"  {line}", color="GREEN")
            _sleep(0.15, fast)

    _sleep(0.5, fast)
    if USE_RICH:
        console.print("  [bold cyan]Agent state →[/bold cyan] [bold green]MONITORING[/bold green]")
    else:
        _p("  Agent state → MONITORING", bold=True, color="GREEN")
    _sleep(0.5, fast)


def step_portfolio_scan(fast: bool):
    """Step 2: Portfolio scan — mirrors _fetch_portfolio_state()"""
    _hdr("STEP 2 / 9  —  PORTFOLIO SCAN", "Fetching real-time positions from Aave V3 & Compound V3")
    _sep()
    _sleep(0.5, fast)

    if USE_RICH:
        table = Table(title="  Live Portfolio Positions", box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("Protocol", style="green", no_wrap=True)
        table.add_column("Asset", style="yellow", no_wrap=True)
        table.add_column("Action", style="magenta")
        table.add_column("Amount", justify="right")
        table.add_column("Value (USD)", justify="right", style="bold")
        table.add_column("APY", justify="right", style="green")
        table.add_column("HF", justify="right")

        for p in PORTFOLIO_POSITIONS:
            hf = str(p["health_factor"])
            action_style = "[red]Borrowed[/red]" if p["action"] == "Borrowed" else "[green]Supplied[/green]"
            hf_style = f"[green]{hf}[/green]" if p["action"] != "Borrowed" else "[dim]-[/dim]"

            table.add_row(
                p["protocol"],
                p["asset"],
                action_style,
                p["amount"],
                f"${p['value_usd']:,.2f}",
                p["apy"],
                hf_style,
            )

        console.print(table)

        total = sum(p["value_usd"] for p in PORTFOLIO_POSITIONS)
        supplied = sum(p["value_usd"] for p in PORTFOLIO_POSITIONS if p["action"] == "Supplied")
        borrowed = sum(p["value_usd"] for p in PORTFOLIO_POSITIONS if p["action"] == "Borrowed")
        debt_ratio = (borrowed / supplied * 100) if supplied else 0

        console.print()
        summary_table = Table(box=box.ROUNDED, show_header=False)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", justify="right", style="bold")
        summary_table.add_row("Total Portfolio Value", f"${total:,.2f}")
        summary_table.add_row("Total Supplied", f"${supplied:,.2f}")
        summary_table.add_row("Total Borrowed", f"${borrowed:,.2f}")
        summary_table.add_row("Debt Ratio", f"{debt_ratio:.1f}%")
        summary_table.add_row("Avg Health Factor", "2.87 [green](safe)[/green]")
        summary_table.add_row("Protocols", "Aave V3, Compound V3")
        console.print(summary_table)
    else:
        header_fmt = "  {:<14} {:<8} {:<10} {:>10} {:>14} {:>8} {:>6}"
        _p(header_fmt.format("Protocol", "Asset", "Action", "Amount", "Value (USD)", "APY", "HF"), bold=True, color="CYAN")
        _p("  " + "─" * 72)
        for p in PORTFOLIO_POSITIONS:
            hf = str(p["health_factor"])
            action_color = "RED" if p["action"] == "Borrowed" else "GREEN"
            _p(header_fmt.format(p["protocol"], p["asset"], p["action"], p["amount"], f"${p['value_usd']:,.2f}", p["apy"], hf), color=action_color)

    _sleep(1.0, fast)


def step_liquidation_shield(fast: bool):
    """Step 3: Liquidation shield — mirrors LiquidationShield.analyze()"""
    _hdr("STEP 3 / 9  —  LIQUIDATION SHIELD", "Monitoring health factors and liquidation risk")
    _sep()
    _sleep(0.5, fast)

    if USE_RICH:
        console.print("  [dim]Running LiquidationShield analysis...[/dim]")
        _sleep(0.5, fast)

        console.print()
        console.print(Panel(
            "[bold yellow]⚠ WARNING DETECTED[/bold yellow]\n\n"
            "  Position: [bold]WETH on Aave V3[/bold]\n"
            "  Current Health Factor: [bold red]1.52[/bold red]\n"
            "  Liquidation Threshold: [bold]1.50[/bold]\n"
            "  Margin: [bold red]1.3%[/bold red] (CRITICAL)\n"
            "  Trigger: ETH price dropped [bold red]-3.2%[/bold red] in last 24h\n\n"
            "  [bold]Recommended Action:[/bold] Repay $2,000 USDC or supply additional collateral\n"
            "  [bold]Risk Level:[/bold] [red]HIGH[/red] — Auto-execution enabled (priority=1)",
            title="[bold red]🛡  LIQUIDATION SHIELD ALERT[/bold red]",
            border_style="red",
            box=box.ROUNDED,
        ))

        _sleep(0.5, fast)
        console.print()
        console.print("  [bold green]✓[/bold green] Shield engaged — auto-protection mode active")
        console.print("  [bold green]✓[/bold green] Auto-approve threshold: $5,000 (this action: $2,000 — [bold green]WITHIN LIMIT[/bold green])")
    else:
        _p("  Running LiquidationShield analysis...", color="DIM")
        _sleep(0.5, fast)
        _p("  ⚠ WARNING: WETH on Aave V3 — Health Factor 1.52 (threshold 1.50)", bold=True, color="YELLOW")
        _p("  Risk Level: HIGH — Auto-execution enabled (priority=1)", bold=True, color="RED")
        _p("  Recommended: Repay $2,000 USDC or supply additional collateral", color="YELLOW")
        _sleep(0.5, fast)
        _p("  ✓ Shield engaged — auto-protection mode active", color="GREEN")

    _sleep(1.0, fast)


def step_llm_reasoning(fast: bool):
    """Step 4: LLM reasoning — mirrors DeFiSentinelAgent._llm_decision()"""
    _hdr("STEP 4 / 9  —  LLM REASONING", "AI agent analyzing and synthesizing decisions")
    _sep()
    _sleep(0.5, fast)

    if USE_RICH:
        console.print("  [dim]Sending portfolio state + recommendations to LLM...[/dim]")
        console.print("  [dim]Model: gpt-4o-mini | Temperature: 0.1 | Max tokens: 2000[/dim]")
        console.print()

        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold cyan]{task.description}[/bold cyan]"),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        ) as progress:
            task = progress.add_task("Reasoning", total=len(LLM_REASONING_STEPS))
            for i, (step, detail) in enumerate(LLM_REASONING_STEPS):
                progress.update(task, description=f"[bold]{step}[/bold]", completed=i + 1)
                console.print(f"    [dim]  → {detail}[/dim]")
                _sleep(0.6, fast)

        console.print()
        # Show the LLM's structured output — matches AgentDecision.to_dict() schema
        llm_output = {
            "decisions": [
                {
                    "action": "repay_debt",
                    "reason": "WETH position health factor (1.52) approaching liquidation threshold (1.50). Repay $2,000 USDC to restore HF to ~2.10.",
                    "priority": 1,
                    "parameters": {
                        "protocol": "Aave V3",
                        "asset": "USDC",
                        "amount": "2000.00",
                        "underlying_collateral": "WETH",
                    },
                    "estimated_usd_impact": -2000.00,
                    "requires_approval": False,
                    "strategy": "liquidation_shield",
                },
                {
                    "action": "yield_optimize",
                    "reason": "USDC on Compound V3 (4.87% APY) can earn 5.42% on Aave V3. Net gain after gas: $152.55/year.",
                    "priority": 2,
                    "parameters": {
                        "from_protocol": "Compound V3",
                        "to_protocol": "Aave V3",
                        "asset": "USDC",
                        "amount": "28500.00",
                    },
                    "estimated_usd_impact": 152.55,
                    "requires_approval": False,
                    "strategy": "yield_optimizer",
                },
                {
                    "action": "rebalance_portfolio",
                    "reason": "Current debt ratio 32.4% exceeds target 30.0%. Repay $1,200 to restore target allocation.",
                    "priority": 3,
                    "parameters": {
                        "target_debt_ratio": 0.30,
                        "current_debt_ratio": 0.324,
                        "repay_amount": "1200.00",
                    },
                    "estimated_usd_impact": -1200.00,
                    "requires_approval": False,
                    "strategy": "rebalancer",
                },
            ]
        }

        console.print(Panel(
            Syntax(json.dumps(llm_output, indent=2), "json", theme="monokai", line_numbers=False),
            title="[bold yellow]🤖 LLM Structured Output[/bold yellow]",
            border_style="yellow",
            box=box.ROUNDED,
        ))
    else:
        _p("  Sending portfolio state to LLM...", color="DIM")
        for step, detail in LLM_REASONING_STEPS:
            _p(f"  ● {step}: {detail}", color="CYAN")
            _sleep(0.4, fast)

    _sleep(0.5, fast)


def step_keeperhub_simulation(fast: bool):
    """Step 5: KeeperHub simulation — mirrors KeeperHubClient.execute_protocol_action(simulate=True)"""
    _hdr("STEP 5 / 9  —  KEEPERHUB SIMULATION", "Gas estimation & revert check before execution")
    _sep()
    _sleep(0.5, fast)

    if USE_RICH:
        console.print("  [dim]Running simulation via KeeperHub (simulate=True)...[/dim]")
        console.print()

        sim_results = [
            ("TXN 1: repay_debt (Aave V3)", "gas_estimate", "21,450 gas ($6.44)", "revert_check", "PASS ✓"),
            ("TXN 2: supply (Aave V3)", "gas_estimate", "18,920 gas ($5.82)", "revert_check", "PASS ✓"),
            ("TXN 3: rebalance (Compound V3)", "gas_estimate", "24,100 gas ($6.14)", "revert_check", "PASS ✓"),
        ]

        table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("Transaction", style="green")
        table.add_column("Metric", style="yellow")
        table.add_column("Value", justify="right")
        table.add_column("Status", justify="right", style="bold")

        for row in sim_results:
            table.add_row(row[0], row[1], row[2], f"[green]{row[3]}[/green]")

        console.print(table)

        console.print()
        console.print("  [bold]Total Gas Estimate:[/bold] [green]$18.40[/green]  |  [bold]All Revert Checks:[/bold] [green]PASS ✓[/green]")
        console.print("  [bold]Simulation Result:[/bold] [bold green]SAFE TO EXECUTE[/bold green]")
    else:
        _p("  Running simulation via KeeperHub...", color="DIM")
        _p("  TXN 1: repay_debt    — 21,450 gas ($6.44) — PASS", color="GREEN")
        _p("  TXN 2: supply        — 18,920 gas ($5.82) — PASS", color="GREEN")
        _p("  TXN 3: rebalance     — 24,100 gas ($6.14) — PASS", color="GREEN")
        _p("  Total Gas: $18.40 | All checks: PASS", bold=True, color="GREEN")

    _sleep(1.0, fast)


def step_keeperhub_execution(fast: bool):
    """Step 6: KeeperHub execution — mirrors KeeperHubClient.execute_protocol_action()"""
    _hdr("STEP 6 / 9  —  KEEPERHUB EXECUTION", "Submitting transactions on-chain")
    _sep()
    _sleep(0.5, fast)

    if USE_RICH:
        txns = [
            {
                "label": "TXN 1: repay_debt (Aave V3)",
                "hash": "0x7f3a2b8c4d5e6f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3c91d",
                "block": 21_048_372,
                "gas_used": "21,340",
                "status": "CONFIRMED",
            },
            {
                "label": "TXN 2: supply USDC (Aave V3)",
                "hash": "0x9e1d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d",
                "block": 21_048_373,
                "gas_used": "18,812",
                "status": "CONFIRMED",
            },
            {
                "label": "TXN 3: rebalance (Compound V3)",
                "hash": "0x4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b",
                "block": 21_048_374,
                "gas_used": "23,987",
                "status": "CONFIRMED",
            },
        ]

        for txn in txns:
            console.print(f"  [bold]{txn['label']}[/bold]")
            console.print(f"    Hash:    [cyan]{txn['hash']}[/cyan]")
            console.print(f"    Block:   [yellow]{txn['block']:,}[/yellow]  |  Gas: [yellow]{txn['gas_used']}[/yellow]")
            console.print(f"    Status:  [bold green]{txn['status']} ✓[/bold green]")
            console.print()
            _sleep(0.8, fast)

        console.print("  [bold green]All 3 transactions confirmed on-chain ✓[/bold green]")
    else:
        txns = [
            ("TXN 1: repay_debt", "0x7f3a...c91d", "21,048,372", "21,340"),
            ("TXN 2: supply", "0x9e1d...0e9d", "21,048,373", "18,812"),
            ("TXN 3: rebalance", "0x4c3b...4c3b", "21,048,374", "23,987"),
        ]
        for label, h, blk, gas in txns:
            _p(f"  {label}", bold=True)
            _p(f"    Hash: {h} | Block: {blk} | Gas: {gas} | Status: CONFIRMED", color="GREEN")
            _sleep(0.6, fast)

    _sleep(0.5, fast)


def step_yield_optimizer(fast: bool):
    """Step 7: Yield optimizer — mirrors YieldOptimizer.analyze()"""
    _hdr("STEP 7 / 9  —  YIELD OPTIMIZER", "Finding better APR across protocols")
    _sep()
    _sleep(0.5, fast)

    if USE_RICH:
        console.print("  [dim]Scanning Aave V3, Compound V3, Morpho, Euler for optimal yields...[/dim]")
        _sleep(0.5, fast)
        console.print()

        table = Table(title="  Yield Optimization Opportunities", box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("Asset", style="yellow", no_wrap=True)
        table.add_column("Current", style="dim")
        table.add_column("Current APY", justify="right", style="red")
        table.add_column("Better Protocol", style="green")
        table.add_column("Better APY", justify="right", style="bold green")
        table.add_column("Improvement", justify="right", style="bold green")
        table.add_column("Net Annual Gain", justify="right", style="bold green")

        for opp in YIELD_OPPORTUNITIES:
            arrow = "→"
            table.add_row(
                opp["asset"],
                opp["current_protocol"],
                opp["current_apy"],
                f"{opp['better_protocol']}",
                opp["better_apy"],
                f"[green]{arrow} {opp['improvement']}[/green]",
                f"[green]{opp['net_gain']}[/green]",
            )

        console.print(table)
        console.print()
        console.print("  [bold green]✓[/bold green] Yield optimization applied — [bold]+$487.49/year[/bold] additional yield")
    else:
        _p("  Scanning protocols for optimal yields...", color="DIM")
        _p("  USDC: Compound V3 (4.87%) → Aave V3 (5.42%) = +$152.55/yr", color="GREEN")
        _p("  WBTC: Aave V3 (0.89%) → Morpho (1.47%) = +$334.94/yr", color="GREEN")
        _p("  Total yield improvement: +$487.49/year", bold=True, color="GREEN")

    _sleep(1.0, fast)


def step_rebalance(fast: bool):
    """Step 8: Portfolio rebalance — mirrors PortfolioRebalancer.analyze()"""
    _hdr("STEP 8 / 9  —  PORTFOLIO REBALANCE", "Restoring target allocation ratios")
    _sep()
    _sleep(0.5, fast)

    if USE_RICH:
        console.print("  [dim]Comparing current vs target allocation...[/dim]")
        _sleep(0.5, fast)
        console.print()

        table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("Asset", style="yellow")
        table.add_column("Current %", justify="right")
        table.add_column("Target %", justify="right")
        table.add_column("Delta", justify="right", style="bold")
        table.add_column("Action", justify="right", style="green")

        allocations = [
            ("WETH", "33.6%", "30.0%", "[red]+3.6%[/red]", "[yellow]Reduce[/yellow]"),
            ("WBTC", "23.5%", "25.0%", "[green]-1.5%[/green]", "[green]Increase[/green]"),
            ("USDC", "19.8%", "20.0%", "[green]-0.2%[/green]", "[dim]Hold[/dim]"),
            ("stETH", "15.3%", "15.0%", "[red]+0.3%[/red]", "[dim]Hold[/dim]"),
            ("Cash", "7.8%", "10.0%", "[green]-2.2%[/green]", "[green]Increase[/green]"),
        ]
        for row in allocations:
            table.add_row(*row)

        console.print(table)
        console.print()

        console.print(Panel(
            "[bold]Rebalance Summary[/bold]\n\n"
            "  Debt Ratio: [red]32.4%[/red] → [green]30.0%[/green] (target)\n"
            "  Action: Repay $1,200 USDC on Compound V3\n"
            "  Gas Cost: $6.14\n"
            "  [bold green]Rebalance executed successfully ✓[/bold green]",
            title="[bold blue]📊 REBALANCE COMPLETE[/bold blue]",
            border_style="blue",
            box=box.ROUNDED,
        ))
    else:
        _p("  Comparing current vs target allocation...", color="DIM")
        _p("  Debt Ratio: 32.4% → 30.0% (target)", bold=True)
        _p("  Action: Repay $1,200 USDC on Compound V3", color="GREEN")
        _p("  Rebalance executed successfully ✓", bold=True, color="GREEN")

    _sleep(1.0, fast)


def step_notifications(fast: bool):
    """Step 9: Notifications — mirrors TelegramProvider + DiscordProvider"""
    _hdr("STEP 9 / 9  —  NOTIFICATIONS", "Sending alerts via Telegram & Discord")
    _sep()
    _sleep(0.5, fast)

    if USE_RICH:
        console.print("  [dim]Dispatching notifications...[/dim]")
        _sleep(0.5, fast)
        console.print()

        telegram_msg = (
            "🛡 *DeFi Sentinel Alert*\n\n"
            "⚠ *Liquidation Risk Detected*\n"
            "Position: WETH on Aave V3\n"
            "Health Factor: 1.52 (threshold: 1.50)\n\n"
            "✅ *Auto-Protected*\n"
            "Action: Repaid $2,000 USDC\n"
            "New HF: 2.10\n\n"
            "📊 *Yield Optimized*\n"
            "+$487.49/year additional yield\n\n"
            "🔄 *Portfolio Rebalanced*\n"
            "Debt ratio: 32.4% → 30.0%\n\n"
            "⏰ 2025-07-12 14:32 UTC"
        )

        discord_msg = (
            "||**🛡 DeFi Sentinel — Cycle Complete**||\n"
            "```\n"
            "Positions scanned:  6\n"
            "Alerts triggered:   1 (liquidation shield)\n"
            "TXNs executed:      3 (all confirmed)\n"
            "Gas spent:          $18.40\n"
            "Yield gain:         +$487.49/yr\n"
            "Debt ratio:         32.4% → 30.0%\n"
            "Next scan:          15:02 UTC\n"
            "```"
        )

        col1 = Panel(telegram_msg, title="📱 Telegram", border_style="blue", box=box.ROUNDED)
        col2 = Panel(discord_msg, title="💬 Discord", border_style="magenta", box=box.ROUNDED)

        console.print(Columns([col1, col2], equal=True, expand=True))
        console.print()
        console.print("  [bold green]✓[/bold green] Telegram: [bold]sent[/bold] to @defi_sentinel_alerts (1 subscriber)")
        console.print("  [bold green]✓[/bold green] Discord:  [bold]sent[/bold] to #defi-alerts (webhook)")
    else:
        _p("  Dispatching notifications...", color="DIM")
        _p("  ✓ Telegram: sent to @defi_sentinel_alerts", color="BLUE")
        _p("  ✓ Discord:  sent to #defi-alerts (webhook)", color="MAGENTA")

    _sleep(1.0, fast)


def step_audit_trail(fast: bool):
    """Audit trail — mirrors AuditTrail.get_entries() + get_summary()"""
    _hdr("AUDIT TRAIL", "Immutable log of all agent actions this cycle")
    _sep()
    _sleep(0.5, fast)

    if USE_RICH:
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("Timestamp", style="dim", no_wrap=True)
        table.add_column("Event", style="yellow")
        table.add_column("Detail", style="white")
        table.add_column("Status", justify="right", style="bold")

        status_styles = {
            "OK": "green",
            "DONE": "green",
            "SENT": "cyan",
            "WARN": "yellow",
        }

        for entry in AUDIT_ENTRIES:
            style = status_styles.get(entry["status"], "white")
            table.add_row(
                entry["ts"],
                entry["event"],
                entry["detail"],
                f"[{style}]{entry['status']}[/]",
            )

        console.print(table)
    else:
        for entry in AUDIT_ENTRIES:
            status_color = "GREEN" if entry["status"] in ("OK", "DONE") else "CYAN" if entry["status"] == "SENT" else "YELLOW"
            _p(f"  {entry['ts']}  {entry['event']:<25} {entry['detail']:<50} [{entry['status']}]", color=status_color)

    _sleep(1.0, fast)


def step_final_dashboard(fast: bool):
    """Final summary dashboard."""
    _hdr("DEMO COMPLETE — SUMMARY DASHBOARD", "Full cycle metrics and agent status")
    _sep()
    _sleep(0.5, fast)

    if USE_RICH:
        metrics = [
            ("Cycle Duration", "18.4s", "green"),
            ("Positions Scanned", "6", "cyan"),
            ("Protocols Monitored", "Aave V3, Compound V3", "cyan"),
            ("Alerts Triggered", "1 (liquidation shield)", "yellow"),
            ("LLM Decisions", "3 (1 critical, 2 optimization)", "magenta"),
            ("Transactions Executed", "3 / 3 confirmed", "green"),
            ("Total Gas Spent", "$18.40", "yellow"),
            ("Yield Improvement", "+$487.49/year", "bold green"),
            ("Debt Ratio", "32.4% → 30.0%", "green"),
            ("Health Factor", "1.52 → 2.10 (restored)", "green"),
            ("Notifications Sent", "Telegram ✓  Discord ✓", "cyan"),
            ("Agent State", "MONITORING (next scan in 30m)", "bold green"),
        ]

        table = Table(box=box.ROUNDED, show_header=False, pad_edge=False)
        table.add_column("Metric", style="cyan", ratio=2)
        table.add_column("Value", style="bold", ratio=3)

        for metric, value, style in metrics:
            table.add_row(f"[cyan]{metric}[/cyan]", f"[{style}]{value}[/{style}]")

        console.print(table)
        console.print()

        # Architecture recap — mirrors actual src/ module structure
        console.print(Panel(
            "[bold]DeFi Sentinel Architecture[/bold]\n\n"
            "  [bold]src/agent/core.py[/bold]       → LLM reasoning + decision synthesis\n"
            "  [bold]src/strategies/liquidation_shield.py[/bold] → Real-time HF monitoring + auto-protection\n"
            "  [bold]src/strategies/yield_optimizer.py[/bold] → Cross-protocol APY comparison\n"
            "  [bold]src/strategies/rebalancer.py[/bold] → Target allocation enforcement\n"
            "  [bold]src/keeperhub/client.py[/bold]  → On-chain execution (simulation + broadcast)\n"
            "  [bold]src/notifications/[/bold]       → Telegram + Discord alerts\n"
            "  [bold]src/observability/audit.py[/bold] → Immutable action trail\n\n"
            "  [dim]All components orchestrated by a single autonomous AI agent[/dim]",
            title="[bold]🏗  SYSTEM ARCHITECTURE[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
        ))
        console.print()

        # Key differentiators
        console.print(Panel(
            "[bold]Key Differentiators for Judges[/bold]\n\n"
            "  1. [bold]Fully Autonomous[/bold] — No manual intervention needed\n"
            "  2. [bold]LLM-Driven Decisions[/bold] — GPT-4o-mini synthesizes multi-strategy analysis\n"
            "  3. [bold]KeeperHub Integration[/bold] — Real on-chain execution with simulation\n"
            "  4. [bold]Multi-Strategy[/bold] — LiquidationShield + YieldOptimizer + Rebalancer\n"
            "  5. [bold]Safety First[/bold] — Auto-approve thresholds, revert checks, HF monitoring\n"
            "  6. [bold]Observable[/bold] — Full audit trail, metrics, structured logging\n"
            "  7. [bold]Extensible[/bold] — Plugin architecture for new strategies\n\n"
            "  [dim]Built with Python, OpenAI, KeeperHub, Rich CLI, and more[/dim]",
            title="[bold]⭐  WHY DEFI SENTINEL WINS[/bold]",
            border_style="yellow",
            box=box.ROUNDED,
        ))
        console.print()
    else:
        metrics = [
            ("Cycle Duration", "18.4s"),
            ("Positions Scanned", "6"),
            ("Protocols Monitored", "Aave V3, Compound V3"),
            ("Alerts Triggered", "1 (liquidation shield)"),
            ("LLM Decisions", "3"),
            ("Transactions Executed", "3 / 3 confirmed"),
            ("Total Gas Spent", "$18.40"),
            ("Yield Improvement", "+$487.49/year"),
            ("Debt Ratio", "32.4% → 30.0%"),
            ("Health Factor", "1.52 → 2.10 (restored)"),
            ("Notifications", "Telegram ✓  Discord ✓"),
            ("Agent State", "MONITORING"),
        ]
        for m, v in metrics:
            _p(f"  {m:<25} {v}", color="CYAN")
        print()

    _sep()

    if USE_RICH:
        console.print()
        console.print("[bold green]  DeFi Sentinel — Demo Complete ✓[/bold green]", justify="center")
        console.print(f"  [dim]Recorded at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}[/dim]", justify="center")
        console.print()
    else:
        _p("  DeFi Sentinel — Demo Complete ✓", bold=True, color="GREEN")
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="DeFi Sentinel — Hackathon Demo")
    parser.add_argument("--fast", action="store_true", help="Fast-forward mode (shorter delays)")
    args = parser.parse_args()

    mode = "[FAST MODE]" if args.fast else "[DEMO MODE]"
    speed_label = "⚡" if args.fast else "🎬"

    try:
        # Title
        print_logo()

        if USE_RICH:
            console.print(f"  {speed_label} {mode}  |  Runtime: {'~30s' if args.fast else '~75s'}", style="dim", justify="center")
        else:
            _p(f"  {mode}  |  Runtime: {'~30s' if args.fast else '~75s'}", color="DIM")

        _sep("─", 70, "DIM")

        # Run all steps — mirrors the real monitoring cycle from core.py
        step_initialization(args.fast)
        step_portfolio_scan(args.fast)
        step_liquidation_shield(args.fast)
        step_llm_reasoning(args.fast)
        step_keeperhub_simulation(args.fast)
        step_keeperhub_execution(args.fast)
        step_yield_optimizer(args.fast)
        step_rebalance(args.fast)
        step_notifications(args.fast)
        step_audit_trail(args.fast)
        step_final_dashboard(args.fast)

    except KeyboardInterrupt:
        if USE_RICH:
            console.print("\n[yellow]Demo interrupted by user.[/yellow]")
        else:
            _p("\nDemo interrupted.", color="YELLOW")
        sys.exit(130)
    except Exception as e:
        if USE_RICH:
            console.print(f"\n[red]Demo error: {e}[/red]")
        else:
            _p(f"\nDemo error: {e}", color="RED")
        sys.exit(1)


if __name__ == "__main__":
    main()