# DeFi Sentinel

**Autonomous AI Agent for DeFi Portfolio Management — Executing Onchain via KeeperHub**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![KeeperHub Powered](https://img.shields.io/badge/KeeperHub-Powered-orange.svg)](https://keeperhub.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Sepolia](https://img.shields.io/badge/Testnet-Sepolia-yellow.svg)](https://sepolia.etherscan.io/)

---

## What It Does

DeFi Sentinel is an autonomous AI agent that monitors DeFi portfolios, prevents liquidations, optimizes yields, and rebalances allocations — all executing onchain via KeeperHub. It combines intelligent decision-making with a robust execution layer to protect capital and maximize returns without manual intervention.

Most AI agents can reason about DeFi but fail at onchain execution — gas spikes, MEV extraction, failed transactions, and silent liquidations destroy value. DeFi Sentinel solves this by using KeeperHub as its exclusive execution layer, ensuring reliable, observable, and auditable onchain operations.

---

## KeeperHub Integration

DeFi Sentinel uses KeeperHub as its **exclusive onchain execution layer**. Every transaction, simulation, and workflow flows through KeeperHub's infrastructure.

### MCP Server — Native Tool Discovery & Execution

DeFi Sentinel connects to KeeperHub's MCP (Model Context Protocol) server to discover and invoke onchain tools programmatically. The agent queries available tools at runtime, selects the appropriate one for each strategy action, and executes with structured parameters — no hardcoded contract calls.

```
Agent → MCP Tool Discovery → Tool Selection → Parameter Binding → Execution → Result Parsing
```

### Workflow Builder — AI-Generated Workflows for Complex DeFi Operations

Multi-step DeFi operations are composed as KeeperHub workflows. The agent generates workflow definitions dynamically:

1. **Decompose** — Break a complex goal (e.g., "rebalance portfolio to target allocation") into discrete onchain steps
2. **Sequence** — Order steps with dependencies (withdraw from Protocol A → swap → deposit to Protocol B)
3. **Execute** — Run the workflow through KeeperHub's orchestration engine with per-step simulation and rollback

### x402 / MPP — Pay-Per-Execution Over HTTP, Settled Onchain

Every KeeperHub tool invocation is a paid service. DeFi Sentinel uses the x402 protocol (Modified Pay Per Request) to:

- Attach payment credentials to each HTTP request to KeeperHub
- Settle payments onchain in real time
- Pay only for successful executions — failed simulations cost nothing
- Maintain a running balance without pre-funding large gas reserves

### Smart Gas Estimation — Adaptive Pricing with Exponential Backoff

Gas management is handled end-to-end by KeeperHub's estimation engine:

- **Pre-flight simulation** estimates gas before any transaction is sent
- **Adaptive pricing** adjusts gas limits based on recent network conditions
- **Exponential backoff** retries failed transactions with increasing delays and adjusted gas
- **Circuit breakers** halt execution if gas costs exceed configurable thresholds

### Private Routing — MEV Protection

KeeperHub's private transaction routing protects DeFi Sentinel from:

- **Front-running** — transactions bypass the public mempool
- **Sandwich attacks** — private ordering prevents exploitable sequencing
- **MEV extraction** — confidential routing hides transaction intent until settlement

### Audit Trail — Full Execution Transparency

Every action is logged with complete context:

| Field | Example |
|---|---|
| **Trigger** | `liquidation_shield: health_factor < 1.2` |
| **Simulation** | `gas_estimate: 185,000 \| revert: false` |
| **Transaction** | `0x9c0274bbdbe13e59c79e86b9547b9a174925610030b331c67e1318829cfb7589` |
| **Gas Used** | `142,380 / 185,000` |
| **Outcome** | `success \| block: 11429034` |

Logs are persisted in JSONL format and exposed as Prometheus metrics for real-time monitoring.

### Protocol Actions — DeFi Integration via KeeperHub Plugins

DeFi Sentinel interacts with major DeFi protocols through KeeperHub's plugin system:

| Protocol | Actions |
|---|---|
| **Aave** | Supply, borrow, repay, withdraw, health factor monitoring |
| **Compound** | Supply, borrow, repay, withdrawal, cToken management |
| **Morpho** | Deposit, withdraw, optimized lending positions |
| **Yearn** | Vault deposits, yield strategy switching, impermanent loss monitoring |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       DeFi Sentinel Agent                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐                                               │
│  │   LLM Engine  │  OpenAI / Anthropic — structured JSON output  │
│  └──────┬───────┘                                               │
│         │                                                       │
│  ┌──────▼──────────────────────────────────────────────────┐    │
│  │                   Strategy Engine                        │    │
│  │                                                          │    │
│  │  ┌──────────────────┐  ┌──────────────────┐             │    │
│  │  │ Liquidation      │  │ Yield            │             │    │
│  │  │ Shield           │  │ Optimizer        │             │    │
│  │  └──────────────────┘  └──────────────────┘             │    │
│  │  ┌──────────────────┐                                   │    │
│  │  │ Portfolio        │                                   │    │
│  │  │ Rebalancer       │                                   │    │
│  │  └──────────────────┘                                   │    │
│  └──────────────────┬───────────────────────────────────────┘    │
│                     │                                            │
│  ┌──────────────────▼────────────────────────────────────────┐   │
│  │              KeeperHub Execution Layer                     │   │
│  │                                                            │   │
│  │  MCP Server  │  Workflow Builder  │  x402/MPP  │  Gas      │   │
│  │  Tool Disc.  │  AI Workflows      │  Pay/Exec  │  Estimation│  │
│  │              │                    │            │  Private   │   │
│  │              │                    │            │  Routing   │   │
│  └──────────────────┬─────────────────────────────────────────┘   │
│                     │                                             │
│  ┌──────────────────▼────────────────────────────────────────┐   │
│  │                      Onchain                               │   │
│  │  Aave │ Compound │ Morpho │ Yearn │ ERC-20 Transfers       │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Observability & Audit                         │   │
│  │  JSONL Audit Trail  │  Prometheus Metrics  │  Notifications │  │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Transaction Proof

Three verified onchain transactions executed through KeeperHub:

### Transaction #1 — Initial Verification (Ethereum Sepolia)

**[`0x164acc244ac007de47056c522b8f3da79e34eb39bbde13bf6adb97f89c85e623`](https://sepolia.etherscan.io/tx/0x164acc244ac007de47056c522b8f3da79e34eb39bbde13bf6adb97f89c85e623)**

| Detail | Value |
|---|---|
| **Chain** | Ethereum Sepolia |
| **Amount** | 0.0001 ETH |
| **Status** | ✅ Completed |
| **Block** | 11429034 |
| **Gas** | Sponsored (KeeperHub) |
| **Wallet** | `0x749B59edC27F53E74fF93A6ef32a57be6E5F05f3` (KeeperHub Agentic Wallet) |

### Transaction #2 — Full Demo Execution (Base Sepolia)

**[`0x9c0274bbdbe13e59c79e86b9547b9a174925610030b331c67e1318829cfb7589`](https://sepolia.basescan.org/tx/0x9c0274bbdbe13e59c79e86b9547b9a174925610030b331c67e1318829cfb7589)**

| Detail | Value |
|---|---|
| **Chain** | Base Sepolia |
| **Amount** | 0.001 BASE |
| **Status** | ✅ Completed |
| **Execution ID** | `we010j8t69ao3ack764ol` |
| **Method** | Full demo: simulation → execution → audit trail |
| **Wallet** | `0x749B59edC27F53E74fF93A6ef32a57be6E5F05f3` (KeeperHub Agentic Wallet) |

### Transaction #3 — Second Verification (Base Sepolia)

**[`0x9a9668a32a18637c86d5484bcf57820fa282bed9f841337f5c0c3889d5c5ba97`](https://sepolia.basescan.org/tx/0x9a9668a32a18637c86d5484bcf57820fa282bed9f841337f5c0c3889d5c5ba97)**

| Detail | Value |
|---|---|
| **Chain** | Base Sepolia |
| **Amount** | 0.001 BASE |
| **Status** | ✅ Completed |
| **Block** | 45114144 |
| **Wallet** | `0x749B59edC27F53E74fF93A6ef32a57be6E5F05f3` (KeeperHub Agentic Wallet) |

All three transactions were executed through the KeeperHub MCP server using JSON-RPC 2.0 over Streamable HTTP, with pre-execution simulation, idempotency keys, and full audit trail logging.

---

## How to Run

### Prerequisites

- Python 3.11+
- KeeperHub API key ([get one](https://app.keeperhub.com))
- LLM API key (OpenAI or Anthropic)

### Setup

```bash
# Clone and enter the project
git clone https://github.com/Carlys17/defi-sentinel.git
cd defi-sentinel

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev,telegram]"

# Configure environment variables
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# LLM Provider
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# KeeperHub
KEEPERHUB_API_KEY=kh-your-key-here
KEEPERHUB_CHAIN=base_sepolia

# Portfolio Settings
PORTFOLIO_REBALANCE_THRESHOLD=5.0
LIQUIDATION_THRESHOLD=1.5
MONITOR_INTERVAL_SECONDS=60
```

### Run

```bash
# Test MCP connection
python scripts/test_mcp.py

# Execute first onchain transaction
python scripts/execute_first_tx.py

# Run the full hackathon demo
python scripts/hackathon_demo.py
```

---

## Scripts

| Script | Description |
|---|---|
| `execute_first_tx.py` | Execute the first onchain transfer via KeeperHub — validates wallet, gas estimation, and tx submission end-to-end |
| `execute_workflow.py` | AI workflow generation and execution — composes multi-step DeFi operations through KeeperHub's workflow builder |
| `execute_real_tx.py` | Direct onchain execution — sends a real transaction through KeeperHub with full simulation and audit logging |
| `execute_onchain.py` | Full execution flow — strategy detection → LLM decision → KeeperHub simulation → onchain execution → audit trail |
| `hackathon_demo.py` | Full demo with simulation + execution — showcases the complete agent loop including strategy evaluation, workflow generation, and onchain settlement |
| `quick_start.py` | Quick start guide — validates configuration, tests MCP connectivity, and walks through a sample execution |
| `test_mcp.py` | MCP connection test — verifies KeeperHub MCP server connectivity and tool discovery |

---

## Strategies

### Liquidation Shield

Monitors health factors across lending protocols (Aave, Compound, Morpho) with a three-tier alert system. When a position approaches liquidation threshold, the agent automatically adds collateral or repays debt — executing onchain via KeeperHub before the protocol can liquidate.

### Yield Optimizer

Scans APRs across Aave, Compound, Morpho, Yearn, and more. Calculates risk-adjusted returns and automatically reallocates capital when a better yield opportunity is detected — accounting for slippage, gas costs, and lock-up periods.

### Portfolio Rebalancer

Maintains target asset allocation percentages with a configurable deviation threshold. Triggers rebalancing trades only when the benefit outweighs gas costs, executing swaps and deposits through KeeperHub's private routing to minimize MEV exposure.

---

## Reliability & Observability

### Retry Logic & Exponential Backoff

Every KeeperHub execution uses automatic retry with exponential backoff. Failed transactions are re-simulated, gas is re-estimated, and the transaction is re-submitted with adjusted parameters — up to a configurable maximum retry count.

### Prometheus Metrics

Real-time metrics are exposed for monitoring and alerting:

- `defi_sentinel_transactions_total` — total transactions executed
- `defi_sentinel_simulation_failures_total` — failed pre-flight simulations
- `defi_sentinel_gas_used_bytes` — gas consumed per transaction
- `defi_sentinel_health_factor_gauge` — current portfolio health factors
- `defi_sentinel_strategy_duration_seconds` — strategy execution latency

### Audit Trail

Every action is logged to JSONL with full context: trigger reason, LLM decision, simulation result, transaction hash, gas used, and final outcome. The audit trail is append-only and serves as the single source of truth for all agent activity.

---

## Project Structure

```
defi-sentinel/
├── config/
│   ├── __init__.py
│   └── settings.py                      # Pydantic settings with env loading
├── demo/
│   ├── demo_video.mp4
│   ├── shot1_logo.cast
│   ├── shot4_demo.cast
│   └── shot7_transactions.cast
├── scripts/
│   ├── execute_first_tx.py              # Execute first onchain transfer
│   ├── execute_onchain.py               # Full execution flow
│   ├── execute_real_tx.py               # Direct onchain execution
│   ├── execute_workflow.py              # AI workflow generation and execution
│   ├── hackathon_demo.py                # Full demo with simulation + execution
│   ├── quick_start.py                   # Quick start guide
│   ├── run_demo.sh                      # Demo runner script
│   └── test_mcp.py                      # MCP connection test
├── src/
│   ├── __init__.py
│   ├── main.py                          # CLI entry point (Typer)
│   ├── agent/
│   │   ├── __init__.py
│   │   └── core.py                      # Main AI agent engine + LLM client
│   ├── keeperhub/
│   │   ├── __init__.py
│   │   └── client.py                    # KeeperHub MCP client
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── liquidation_shield.py        # Liquidation protection
│   │   ├── yield_optimizer.py           # Yield optimization
│   │   └── rebalancer.py                # Portfolio rebalancing
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── base.py                      # Abstract notification interface
│   │   ├── telegram.py                  # Telegram provider
│   │   ├── discord.py                   # Discord provider
│   │   └── logger_provider.py           # Logger fallback
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── audit.py                     # Audit trail system
│   │   └── metrics.py                   # Prometheus metrics
│   └── utils/
│       ├── __init__.py
│       └── helpers.py                   # Utility functions
├── tests/
│   ├── __init__.py
│   ├── test_helpers.py
│   ├── test_keeperhub_client.py         # KeeperHub MCP client tests
│   └── test_settings.py
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── .github/
│   └── workflows/
│       └── ci.yml                       # CI: ruff, mypy, pytest
├── DEMO_GUIDE.md
├── Dockerfile
├── docker-compose.yml
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── SUBMISSION.md
└── README.md
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

Built for the **KeeperHub Agents Onchain Hackathon**.

Powered by [KeeperHub](https://keeperhub.com/) — the execution and reliability layer for AI agents operating onchain.