# 🛡️ DeFi Sentinel

**Autonomous AI Agent for DeFi Portfolio Management & Risk Protection**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![KeeperHub](https://img.shields.io/badge/KeeperHub-Powered-orange.svg)](https://keeperhub.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![DoraHacks](https://img.shields.io/badge/DoraHacks-Agents%20Onchain-red.svg)](https://dorahacks.io/hackathon/agents-onchain)

---

## Overview

DeFi Sentinel is a production-grade autonomous AI agent that manages DeFi portfolios onchain through **KeeperHub's execution and reliability layer**. It combines intelligent decision-making with robust onchain execution to protect capital, optimize yields, and maintain portfolio balance — all without manual intervention.

### Why DeFi Sentinel?

Most AI agents can reason about DeFi, but fail when it comes to **onchain execution** — gas spikes, MEV extraction, failed transactions, and silent liquidations destroy value. DeFi Sentinel solves this by using KeeperHub as its execution layer, ensuring:

- ✅ **Reliable execution** with automatic retries, gas estimation, and failure handling
- ✅ **MEV protection** through KeeperHub's transaction ordering
- ✅ **Full audit trail** of every decision and transaction
- ✅ **Real-time monitoring** with configurable alerting
- ✅ **Safety-first** design with approval thresholds and circuit breakers

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DeFi Sentinel Agent                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────────────────────────┐   │
│  │   LLM Engine  │    │        Strategy Engine           │   │
│  │              │    │                                  │   │
│  │  • OpenAI    │    │  ┌────────────────────────────┐  │   │
│  │  • Anthropic │───▶│  │  Liquidation Shield        │  │   │
│  │  • Structured│    │  │  - Health factor monitoring │  │   │
│  │    JSON      │    │  │  - Auto collateral/repay    │  │   │
│  └──────────────┘    │  └────────────────────────────┘  │   │
│                      │  ┌────────────────────────────┐  │   │
│                      │  │  Yield Optimizer           │  │   │
│                      │  │  - Cross-protocol APR scan  │  │   │
│                      │  │  - Risk-adjusted returns    │  │   │
│                      │  └────────────────────────────┘  │   │
│                      │  ┌────────────────────────────┐  │   │
│                      │  │  Portfolio Rebalancer       │  │   │
│                      │  │  - Target allocation        │  │   │
│                      │  │  - Auto rebalance           │  │   │
│                      │  └────────────────────────────┘  │   │
│                      └──────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              KeeperHub MCP Client                     │   │
│  │  • Workflow execution  • DeFi protocol actions       │   │
│  │  • Direct transfers    • Contract calls              │   │
│  │  • Simulation mode     • Idempotency keys            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Observability Layer                      │   │
│  │  • Audit trail (JSONL)  • Prometheus metrics         │   │
│  │  • Structured logging   • Health checks              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Notification Layer                       │   │
│  │  • Telegram  • Discord  • Logger                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

### 🛡️ Liquidation Shield
- Monitors health factors across lending protocols (Aave, Compound, Morpho)
- Three-tier alert system: Info → Warning → Critical
- Automatic collateral addition and debt repayment
- Emergency mode: auto-execute without approval when liquidation is imminent

### 📈 Yield Optimizer
- Scans APRs across Aave, Compound, Morpho, Yearn, Spark, and more
- Risk-adjusted return calculation
- Automatic capital reallocation when better yields are found
- Slippage and gas cost awareness

### ⚖️ Portfolio Rebalancer
- Maintains target allocation percentages
- Configurable deviation threshold
- Smart rebalancing that considers gas costs vs. rebalance benefit

### 🔐 Safety & Reliability
- **Simulation-first**: Every transaction is simulated before execution
- **Idempotency keys**: Retry-safe execution without double-spending
- **Approval thresholds**: Auto-approve small transactions, require approval for large ones
- **Circuit breakers**: Block transactions above configurable USD limits
- **Exponential backoff**: Automatic retries with smart delay

### 📊 Observability
- Full audit trail in JSONL format
- Prometheus metrics for monitoring and alerting
- Structured logging with correlation IDs
- Real-time portfolio snapshots

---

## Quick Start

### Prerequisites

- Python 3.11+
- KeeperHub API key ([get one here](https://app.keeperhub.com))
- LLM API key (OpenAI or Anthropic)

### Installation

```bash
# Clone the repository
git clone https://github.com/Carlys17/defi-sentinel.git
cd defi-sentinel

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev,telegram]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings
```

### Configuration

Edit `.env` with your settings:

```env
# LLM Provider
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# KeeperHub
KEEPERHUB_API_KEY=kh-your-key-here
KEEPERHUB_CHAIN=base_sepolia

# Portfolio
PORTFOLIO_REBALANCE_THRESHOLD=5.0
LIQUIDATION_THRESHOLD=1.5
MONITOR_INTERVAL_SECONDS=60
```

### Running

```bash
# Check configuration
defi-sentinel status

# Run health checks
defi-sentinel check

# Execute your first onchain transaction
python scripts/quick_start.py          # Real transaction
python scripts/quick_start.py --simulate  # Simulation only

# Start the agent
defi-sentinel start

# Start with custom interval
defi-sentinel start --interval 30
```

### Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f defi-sentinel
```

---

## KeeperHub Integration

DeFi Sentinel uses KeeperHub as its **exclusive onchain execution layer**, leveraging:

| KeeperHub Surface | Usage in DeFi Sentinel |
|---|---|
| **MCP Server** | 30+ tools for workflow management, execution, and monitoring |
| **DeFi Plugins** | Aave v3/v4, Compound, Morpho, Yearn, Uniswap, CowSwap |
| **Agentic Wallet** | Server-side Turnkey custody, gasless payments via x402 |
| **Workflow Builder** | Visual automation for complex multi-step operations |
| **Audit Trail** | Full execution logs with error context |
| **CLI (`kh`)** | Programmatic resource management |
| **x402/MPP** | Pay-per-execution over HTTP, settled onchain |

### Execution Flow

```
1. Strategy detects opportunity/risk
2. Agent generates decision with LLM reasoning
3. KeeperHub simulates transaction (gas estimate + revert check)
4. If simulation passes, execute with idempotency key
5. Monitor execution status via get_direct_execution_status
6. Log to audit trail and notify via Telegram/Discord
```

### Onchain Execution Scripts

```bash
# Quick start - execute first transaction
python scripts/quick_start.py

# Full execution flow with all KeeperHub tools
python scripts/execute_onchain.py

# Simulation mode (no broadcast)
python scripts/execute_onchain.py --simulate

# Execute specific transfer
python scripts/execute_onchain.py --transfer --to 0x... --amount "1000000000000000"

# Check execution status
python scripts/execute_onchain.py --status --execution-id <id>
```

### Transaction History
All executed transactions are logged in:
- `logs/execution_results.json` - Structured execution results
- `logs/audit.jsonl` - Full audit trail with timestamps

### ✅ Verified Onchain Transactions

> **Transaction 1:** [`0xc244ad7e2ea2235161f51813524c330f53ad8214f9ba69c698cda127483ff429`](https://sepolia.basescan.org/tx/0xc244ad7e2ea2235161f51813524c330f53ad8214f9ba69c698cda127483ff429)
>
> **Transaction 2:** [`0x9a9668a32a18637c86d5484bcf57820fa282bed9f841337f5c0c3889d5c5ba97`](https://sepolia.basescan.org/tx/0x9a9668a32a18637c86d5484bcf57820fa282bed9f841337f5c0c3889d5c5ba97)
>
> **Chain:** Base Sepolia (84532)
> **Amount:** 0.001 BASE each
> **Status:** ✅ Both Completed
> **Executed via:** KeeperHub MCP Server

---

## Project Structure

```
defi-sentinel/
├── config/
│   ├── __init__.py
│   └── settings.py          # Pydantic settings with env loading
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI entry point (Typer)
│   ├── agent/
│   │   ├── __init__.py
│   │   └── core.py          # Main AI agent engine + LLM client
│   ├── keeperhub/
│   │   ├── __init__.py
│   │   └── client.py        # KeeperHub MCP client
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── liquidation_shield.py   # Liquidation protection
│   │   ├── yield_optimizer.py      # Yield optimization
│   │   └── rebalancer.py           # Portfolio rebalancing
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract notification interface
│   │   ├── telegram.py          # Telegram provider
│   │   ├── discord.py           # Discord provider
│   │   └── logger_provider.py   # Logger fallback
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── audit.py             # Audit trail system
│   │   └── metrics.py           # Prometheus metrics
│   └── utils/
│       ├── __init__.py
│       └── helpers.py           # Utility functions
├── tests/
│   ├── __init__.py
│   ├── test_settings.py
│   └── test_helpers.py
├── scripts/
│   └── run_demo.sh
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Supported Protocols & Chains

### Protocols (via KeeperHub DeFi Plugins)
- **Lending:** Aave v3/v4, Compound, Morpho, Spark
- **DEX:** Uniswap, CowSwap, Curve, Aerodrome
- **Yield:** Yearn v3, Pendle, Ethena, Lido, Rocket Pool
- **Infrastructure:** Chainlink, Superfluid, Safe

### Chains
- Base (Mainnet + Sepolia)
- Arbitrum (Mainnet + Sepolia)
- Polygon (Mainnet + Mumbai)
- Ethereum Mainnet

---

## Judging Criteria Alignment

| Criteria | How DeFi Sentinel Delivers |
|---|---|
| **Execution** | Real onchain transactions via KeeperHub — no mockups |
| **KeeperHub Surfaces** | MCP server, DeFi plugins, agentic wallet, workflow builder, audit trail, CLI |
| **Reliability** | Simulation-first, idempotency keys, exponential backoff, retry logic, circuit breakers |
| **Observability** | Full audit trail, Prometheus metrics, structured logging, notification alerts |
| **Originality** | Production-grade autonomous agent solving real DeFi problems |
| **Integration Quality** | Clean architecture, type-safe Pydantic config, CLI, Docker, tests |

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Format code
ruff check --fix .
ruff format .

# Type check
mypy src/

# Setup pre-commit hooks
pre-commit install
```

---

## Roadmap

- [ ] Multi-wallet support
- [ ] Custom strategy plugin system
- [ ] Web dashboard for monitoring
- [ ] MEV protection via CowSwap integration
- [ ] Cross-chain execution
- [ ] Natural language command interface

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

Built for the **KeeperHub — Agents Onchain Hackathon** on [DoraHacks](https://dorahacks.io/hackathon/agents-onchain).

Powered by [KeeperHub](https://keeperhub.com/) — the execution and reliability layer for AI agents operating onchain.