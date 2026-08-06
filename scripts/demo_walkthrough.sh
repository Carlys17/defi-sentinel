#!/bin/bash
# DeFi Sentinel — demo walkthrough for video recording
# Runs the real pipeline: KeeperHub MCP live demo, agent cycle, onchain proof.
# Designed for a 140x40 widescreen terminal.

type_cmd() {
  # Print command char-by-char for a "live typing" effect, then run it
  local cmd="$1"
  printf '\033[1;36m$ %s\033[0m' "$cmd"
  sleep 0.8
  printf '\n'
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
sleep 4

echo '──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────'
printf '\033[1;33m[1/6] THE PROBLEM\033[0m\n'
cat << 'EOF'
  Agents can detect and decide — but they hit the same wall when they
  must move value onchain: failed transactions, gas spikes, MEV,
  no retries, no observability, no guarantees.

  DeFi Sentinel bridges decision -> execution through KeeperHub:
  simulation first, then reliable broadcast with idempotency keys.
EOF
sleep 4

echo '──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────'
printf '\033[1;33m[2/6] ARCHITECTURE\033[0m\n\n'
cat << 'EOF'
  LLM Engine (OpenAI)          -> structured decisions (JSON)
  Strategy Engine              -> LiquidationShield / YieldOptimizer / Rebalancer
  KeeperHub MCP Client         -> simulation + onchain execution (Base Sepolia)
  Observability                -> audit trail + Prometheus metrics
EOF
printf '\n  \033[90mSource layout:\033[0m\n'
sleep 1
find src -name "*.py" | sort | sed 's/^/    /'
sleep 3

echo '──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────'
printf '\033[1;33m[3/6] KEEPERHUB INTEGRATION — LIVE\033[0m\n\n'
type_cmd ". .venv/bin/activate"
type_cmd "python scripts/hackathon_demo.py --simulate"
sleep 3

echo '──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────'
printf '\033[1;33m[4/6] FULL AGENT CYCLE (SIMULATED MARKET DATA)\033[0m\n\n'
type_cmd "python scripts/demo.py"
sleep 3

echo '──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────'
printf '\033[1;33m[5/6] PROOF OF REAL ONCHAIN TRANSACTIONS — BASE SEPOLIA\033[0m\n\n'
TX1=0xc244ad7e2ea2235161f51813524c330f53ad8214f9ba69c698cda127483ff429
TX2=0x9a9668a32a18637c86d5484bcf57820fa282bed9f841337f5c0c3889d5c5ba97
printf '  \033[1mTx #1:\033[0m %s\n' "$TX1"
printf '  \033[1mTx #2:\033[0m %s\n\n' "$TX2"
printf '  \033[90mVerifying receipts directly against Base Sepolia RPC...\033[0m\n'
sleep 1
curl -s -X POST https://sepolia.base.org -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_getTransactionReceipt\",\"params\":[\"$TX1\"],\"id\":1}" \
  | python3 -c "import sys,json; r=json.load(sys.stdin)['result']; print(f\"  Tx #1 receipt -> block {int(r['blockNumber'],16)}, gasUsed {int(r['gasUsed'],16)}, status {'SUCCESS' if r['status']=='0x1' else 'REVERTED'}\")"
sleep 1
curl -s -X POST https://sepolia.base.org -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_getTransactionReceipt\",\"params\":[\"$TX2\"],\"id\":2}" \
  | python3 -c "import sys,json; r=json.load(sys.stdin)['result']; print(f\"  Tx #2 receipt -> block {int(r['blockNumber'],16)}, gasUsed {int(r['gasUsed'],16)}, status {'SUCCESS' if r['status']=='0x1' else 'REVERTED'}\")"
printf '\n  \033[90mExplorer:\033[0m\n'
printf '    https://sepolia.basescan.org/tx/%s\n' "$TX1"
printf '    https://sepolia.basescan.org/tx/%s\n' "$TX2"
sleep 4

echo '──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────'
printf '\033[1;33m[6/6] SAFETY & OBSERVABILITY\033[0m\n\n'
printf '  \033[1mAudit trail (logs/audit.jsonl) — last 2 events:\033[0m\n'
tail -2 logs/audit.jsonl 2>/dev/null | python3 -m json.tool 2>/dev/null | sed 's/^/    /'
printf '\n  \033[1mSafety rails:\033[0m\n'
printf '    - Simulation before every execution (wouldRevert check)\n'
printf '    - Idempotency keys for retry-safe broadcasts\n'
printf '    - Spending caps: AUTO_APPROVE_MAX_USD / BLOCK_THRESHOLD_USD\n'
printf '    - Health-factor thresholds: warn 1.5, emergency 1.2\n'
sleep 4

echo '──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────'
printf '\n\033[1;32m  DeFi Sentinel — detection, reasoning, and execution. All onchain. All auditable.\033[0m\n'
printf '\033[90m  github.com/Carlys17/defi-sentinel  |  KeeperHub execution layer  |  Base Sepolia\033[0m\n\n'
sleep 4
