#!/bin/bash
# DeFi Sentinel v7 walkthrough — 95s total (8 intro + 79 main + 8 outro)
# Each section timed to match the brief exactly.

type_cmd() {
  local cmd="$1"
  printf '\033[1;36m$ %s\033[0m\n' "$cmd"
  sleep 0.8
  eval "$cmd"
}

clear
printf '\n\033[1;32m  ██████╗ ███████╗███████╗██╗    ██╗  ██╗███████╗██╗     ██╗███╗   ██╗███████╗████████╗\033[0m\n'
printf '\033[1;32m  ██╔══██╗██╔════╝██╔════╝██║    ██║ ██╔╝██╔════╝██║     ██║████╗  ██║██╔════╝╚══██╔══╝\033[0m\n'
printf '\033[1;32m  ██║  ██║█████╗  █████╗  ██║    █████╔╝ █████╗  ██║     ██║██╔██╗ ██║█████╗     ██║   \033[0m\n'
printf '\033[1;32m  ██║  ██║██╔══╝  ██╔══╝  ██║    ██╔═██╗ ██╔══╝  ██║     ██║██║╚██╗██║██╔══╝     ██║   \033[0m\n'
printf '\033[1;32m  ██████╔╝███████╗██║     ██║    ██║  ██╗███████╗███████╗██║██║ ╚████║███████╗   ██║   \033[0m\n'
printf '\033[1;32m  ╚═════╝ ╚══════╝╚═╝     ╚═╝    ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   \033[0m\n'
printf '\n  \033[1mAutonomous AI Agent for DeFi Portfolio Management & Liquidation Protection\033[0m\n'
printf '  \033[90mExecution layer: KeeperHub  |  Chain: Base Sepolia  |  DoraHacks "Agents Onchain"\033[0m\n\n'
sleep 5

echo '══════════════════════════════════════════════════════════════════════════════════════════════════════════════════'
printf '\033[1;33m[0:08] THE PROBLEM — Failed transactions, gas spikes, MEV, no guarantees\033[0m\n'
cat << 'EOF'
  Your DeFi portfolio never sleeps.
  Manual monitoring can't catch liquidations, MEV, and failed transactions in time.

  DeFi Sentinel bridges detection -> execution through KeeperHub.
  Simulation first, then reliable broadcast with idempotency keys.
EOF
sleep 6

echo '══════════════════════════════════════════════════════════════════════════════════════════════════════════════════'
printf '\033[1;33m[0:20] 3 CORE STRATEGIES — Live Demo\033[0m\n\n'
printf '  \033[1;36mLiquidation Shield\033[0m — monitors Aave V3, Compound V3, Morpho in real time\n'
sleep 2
type_cmd ". .venv/bin/activate"
type_cmd "python scripts/demo.py --fast 2>&1 | sed -n '/LIQUIDATION SHIELD/,/Yield Optimizer/p' | head -18"
sleep 4

echo '══════════════════════════════════════════════════════════════════════════════════════════════════════════════════'
printf '\033[1;33m[0:30] Yield Optimizer — APR scan across protocols, gas-aware reallocation\033[0m\n\n'
type_cmd "python scripts/demo.py --fast 2>&1 | sed -n '/YIELD OPTIMIZER/,/Portfolio Rebalance/p' | head -16"
sleep 4

echo '══════════════════════════════════════════════════════════════════════════════════════════════════════════════════'
printf '\033[1;33m[0:42] Portfolio Rebalancer — target allocation enforcement\033[0m\n\n'
type_cmd "python scripts/demo.py --fast 2>&1 | sed -n '/PORTFOLIO REBALANCE/,/Telegram/p' | head -16"
sleep 4

echo '══════════════════════════════════════════════════════════════════════════════════════════════════════════════════'
printf '\033[1;33m[0:55] PROOF OF REAL ONCHAIN EXECUTION — Base Sepolia\033[0m\n\n'
TX1=0xc244ad7e2ea2235161f51813524c330f53ad8214f9ba69c698cda127483ff429
TX2=0x9a9668a32a18637c86d5484bcf57820fa282bed9f841337f5c0c3889d5c5ba97
printf '  \033[1mTx #1:\033[0m %s\n' "$TX1"
printf '  \033[1mTx #2:\033[0m %s\n\n' "$TX2"
printf '  \033[90mVerifying receipts against Base Sepolia RPC...\033[0m\n'
sleep 1
curl -s -X POST https://sepolia.base.org -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_getTransactionReceipt\",\"params\":[\"$TX1\"],\"id\":1}" \
  | python3 -c "import sys,json; r=json.load(sys.stdin)['result']; print(f\"  Tx #1 -> block {int(r['blockNumber'],16)}, gasUsed {int(r['gasUsed'],16)}, status {'SUCCESS' if r['status']=='0x1' else 'REVERTED'}\")"
sleep 1
curl -s -X POST https://sepolia.base.org -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_getTransactionReceipt\",\"params\":[\"$TX2\"],\"id\":2}" \
  | python3 -c "import sys,json; r=json.load(sys.stdin)['result']; print(f\"  Tx #2 -> block {int(r['blockNumber'],16)}, gasUsed {int(r['gasUsed'],16)}, status {'SUCCESS' if r['status']=='0x1' else 'REVERTED'}\")"
printf '\n  \033[90mExplorer:\033[0m\n'
printf '    https://sepolia.basescan.org/tx/%s\n' "$TX1"
printf '    https://sepolia.basescan.org/tx/%s\n' "$TX2"
sleep 6

echo '══════════════════════════════════════════════════════════════════════════════════════════════════════════════════'
printf '\033[1;33m[0:70] KEEPERHUB ARCHITECTURE — Simulation-first. Idempotent. Safe by design.\033[0m\n\n'
cat << 'EOF'
  LLM Engine (OpenAI/Anthropic)     -> structured JSON decisions
  Strategy Engine                   -> LiquidationShield / YieldOptimizer / Rebalancer
  KeeperHub MCP Client              -> 30+ tools, Agentic Wallet, Workflow Builder
  Execution Layer                   -> Base/Arbitrum/Polygon/Ethereum
  Observability                     -> Audit trail + Prometheus metrics
EOF
sleep 5

echo '══════════════════════════════════════════════════════════════════════════════════════════════════════════════════'
printf '\n\033[1;32m  DeFi Sentinel — Autonomous, Reliable, Verifiably Onchain.\033[0m\n'
printf '\033[90m  github.com/Carlys17/defi-sentinel  |  DoraHacks Agents Onchain  |  Base Sepolia\033[0m\n\n'
sleep 5
