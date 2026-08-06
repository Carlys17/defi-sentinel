# �� 🎬 Video Script — DeFi Sentinel Hackathon Demo

> **Target duration:** 3-4 minutes
> **Language:** English
> **Pacing:** Fast, focused on proof of real onchain execution

---

## Segment 1: Hook (0:00-0:15)

**Visual:** DeFi Sentinel logo + ASCII art in terminal

> "DeFi Sentinel — an autonomous AI agent that doesn't just think, it actually executes onchain transactions. This isn't a mockup. This is real proof."

---

## Segment 2: Problem (0:15-0:40)

**Visual:** Screenshot of a DeFi portfolio with low health factor

> "The problem is simple: most hackathon agents can only reason — they can decide something smart. But the real problem lies in the next step. Agents can detect and decide, but they all hit the same wall when it comes to moving value onchain. Failed transactions, gas spikes, MEV, no observability, no guarantees. KeeperHub is the solution — the last mile between what an agent decides and a transaction that actually works onchain."

---

## Segment 3: Solution & Architecture (0:40-1:20)

**Visual:** Architecture diagram from README

> "DeFi Sentinel is built on top of KeeperHub as its execution layer. Here's the architecture: The LLM Engine — using OpenAI or Anthropic — performs reasoning and outputs structured JSON. The Strategy Engine has three strategies: Liquidation Shield monitors health factor and automatically executes collateral or repay actions; Yield Optimizer scans APR across protocols and reallocates capital; and Portfolio Rebalancer maintains target allocation. All agent decisions are executed via the KeeperHub MCP Client — handling workflow execution, DeFi protocol actions, direct transfers, and contract calls. Simulation-first: every transaction is simulated before it's actually executed."

---

## Segment 4: KeeperHub Integration Demo (1:20-2:10)

**Visual:** Live terminal — run `python3 scripts/hackathon_demo.py --simulate`

> "Now let's see it live in the terminal. I'm running the demo script. First step: MCP session initialized — connection to KeeperHub server via JSON-RPC 2.0. Second step: wallet integration verified — wallet 0x749B... is connected. Third step: action schemas loaded — Aave V3, Compound, Morpho, Yearn, Uniswap, CowSwap are all available. Fourth step: simulation passed — a transfer of 0.001 BASE is simulated, no revert. Fifth step: real execution — and this is the key part — the transaction is actually executed onchain via KeeperHub. Status: COMPLETED."

---

## Segment 5: Proof of Real Onchain Transactions (2:10-2:40)

**Visual:** Open BaseScan explorer for two transactions

> "This isn't simulation. These are real transactions on Base Sepolia. First transaction: 0xc244... — completed. Second transaction: 0x9a96... — also completed. These two transactions were executed directly by the agent via KeeperHub MCP. You can check them yourself on BaseScan. This is what the hackathon wants: working transactions, not mockups."

---

## Segment 6: Safety & Observability (2:40-3:10)

**Visual:** Show audit trail log & metrics

> "Every agent action is recorded in the audit trail: trigger, simulation result, submitted transaction, gas used, outcome, timestamp. Idempotency keys ensure retry-safe execution. Smart gas estimation adapts to network congestion. Prometheus metrics provide observability. All of this ensures the agent doesn't just run — it runs safely and can be audited."

---

## Segment 7: Closing + CTA (3:10-3:30)

**Visual:** GitHub repo link + transaction links

> "DeFi Sentinel — autonomous AI agent for DeFi portfolio management, powered by KeeperHub execution layer. GitHub: github.com/Carlys17/defi-sentinel. Two verified transactions on Base Sepolia. Submitted to DoraHacks Agents Onchain hackathon. Thank you!"

---

## Production Notes

- **Voiceover:** Record separately, sync in post-production
- **BGM:** Instrumental lo-fi/ambient (low volume)
- **Subtitles:** Required (Indonesian + English)
- **Zoom-in:** When showing transaction hash in terminal
- **Highlight:** Use cursor/mouse pointer to guide viewer attention