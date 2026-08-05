# DeFi Sentinel — Demo Recording Guide

> This guide walks you through recording a polished demo video of DeFi Sentinel for your hackathon submission.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [How to Run the Demo](#how-to-run-the-demo)
3. [Recommended Screen Recording Settings](#recommended-screen-recording-settings)
4. [Tips for a Great Demo Video](#tips-for-a-great-demo-video)
5. [What the Judges Will Look For](#what-the-judges-will-look-for)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Install Dependencies

```bash
cd /opt/sandbox/workspace/defi-sentinel

# Install project dependencies (includes rich for beautiful terminal output)
pip install -e ".[dev]"
```

The demo script requires **`rich`** for formatted output. It falls back to ANSI codes if rich is not installed, but the visual quality will be significantly better with rich.

### 2. Set Up `.env` (Optional — Demo Uses Simulated Data)

The demo script **does not require real API keys** — it uses realistic simulated data. However, if you want to also show the real agent running alongside the demo:

```env
# .env
CHAIN_ID=1
CHAIN_NAME=ethereum-mainnet
RPC_URL=https://eth.llamarpc.com
KEEPERHUB_API_KEY=your_keeperhub_key
KEEPERHUB_API_URL=wss://mainnet.keeperhub.network/v1
WALLET_ADDRESS=0x742d...8f3a
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
DISCORD_WEBHOOK_URL=your_discord_webhook_url
```

### 3. Verify Terminal Setup

The demo looks best in a **dark-themed terminal** with a **monospace font**:

- **Recommended terminals**: iTerm2 (macOS), Windows Terminal (Windows), GNOME Terminal (Linux)
- **Recommended fonts**: JetBrains Mono, Fira Code, Cascadia Code, or SF Mono
- **Font size**: 14–16px (large enough to read in a 1080p video)
- **Theme**: Dark background (e.g., One Dark, Monokai, Dracula)

---

## How to Run the Demo

### Normal Mode (~75 seconds)

```bash
python scripts/demo.py
```

This runs the full demo with dramatic pauses between steps, ideal for recording.

### Fast Mode (~30 seconds)

```bash
python scripts/demo.py --fast
```

Use this for quick previews before recording. Delays are shortened to 0.3s max.

### What the Demo Shows

The script simulates the complete agent lifecycle in 9 steps:

| Step | Description | Duration |
|------|-------------|----------|
| 1 | **Initialization** — Config, KeeperHub, LLM, strategies loaded | ~3s |
| 2 | **Portfolio Scan** — 6 positions across Aave V3 & Compound V3 | ~5s |
| 3 | **Liquidation Shield** — Health factor warning detected | ~5s |
| 4 | **LLM Reasoning** — AI thinking process with structured output | ~8s |
| 5 | **KeeperHub Simulation** — Gas estimation & revert checks | ~5s |
| 6 | **KeeperHub Execution** — 3 on-chain transactions confirmed | ~8s |
| 7 | **Yield Optimizer** — Better APR found across protocols | ~5s |
| 8 | **Portfolio Rebalance** — Target allocation restored | ~5s |
| 9 | **Notifications** — Telegram + Discord alerts dispatched | ~5s |
| — | **Audit Trail** — Full cycle log | ~5s |
| — | **Summary Dashboard** — All metrics and architecture overview | ~5s |

---

## Recommended Screen Recording Settings

### Software Options

| Tool | Platform | Notes |
|------|----------|-------|
| **OBS Studio** | All | Free, best quality, supports scene switching |
| **QuickTime** | macOS | Simple, built-in, good enough |
| **ShareX** | Windows | Free, lightweight |
| **ScreenFlow** | macOS | Paid, excellent editing features |

### OBS Studio Setup (Recommended)

1. **Canvas Resolution**: 1920×1080 (1080p)
2. **Output Resolution**: 1920×1080
3. **FPS**: 30 (60 is overkill for terminal output)
4. **Bitrate**: 6000 Kbps (for YouTube) or 8000 Kbps (for high quality)
5. **Encoder**: NVENC (NVIDIA) / AMF (AMD) / QuickSync (Intel) / x264
6. **Rate Control**: CBR (Constant Bitrate)
7. **Format**: MP4 or MKV

### Recording Area

- **Crop to terminal only** — don't record your entire desktop
- Leave a small margin around the terminal window for aesthetics
- Make sure the terminal fills most of the frame

### Audio

- **Narration is optional** — the demo script is self-explanatory
- If adding voiceover: record separately and sync in post-production
- Use a decent USB microphone (Blue Yeti, Fifine, or similar)

---

## Tips for a Great Demo Video

### Before Recording

1. **Clean your terminal** — run `clear` before starting the demo
2. **Close unnecessary tabs/windows** — avoid distractions
3. **Set your terminal to full screen** — maximizes the visible area
4. **Do 2–3 practice runs** — use `--fast` mode for quick previews
5. **Disable notifications** — prevent system popups from appearing

### During Recording

1. **Start recording 5 seconds before** running the script
2. **Say a brief intro** (optional): *"This is DeFi Sentinel, an autonomous AI agent for DeFi portfolio management..."*
3. **Let the script run uninterrupted** — don't click or move the mouse
4. **Wait for the final dashboard** to fully render before stopping

### After Recording

1. **Trim the beginning and end** — remove dead air
2. **Speed up slow sections** (if needed) — the LLM reasoning step can be trimmed
3. **Add intro/outro cards** with your project name and GitHub link
4. **Export as MP4, H.264, 1080p** — universal compatibility

### Video Length Target

- **Ideal**: 1.5–2 minutes
- **Maximum**: 3 minutes (judges have many submissions to review)
- **Minimum**: 45 seconds (show enough to demonstrate the full workflow)

---

## What the Judges Will Look For

### 1. Technical Depth (30%)

- **Real architecture** — not just a UI mockup
- **LLM integration** — how AI makes decisions, not just displays data
- **KeeperHub execution** — real on-chain transaction simulation
- **Multi-strategy design** — LiquidationShield, YieldOptimizer, Rebalancer

### 2. Problem Solving (25%)

- **Clear problem statement** — why does this exist? (DeFi risk management)
- **Realistic scenario** — the liquidation shield demo shows a real pain point
- **Quantified impact** — "$487.49/year yield improvement", "HF restored from 1.52 to 2.10"

### 3. Execution Quality (20%)

- **Polished presentation** — clean terminal output, no errors
- **Complete workflow** — from detection to execution to notification
- **Error handling** — simulation checks, revert guards, safety thresholds

### 4. Innovation (15%)

- **Autonomous agent** — no manual intervention needed
- **AI-driven decisions** — LLM synthesizes multi-strategy analysis
- **KeeperHub integration** — bridges AI reasoning with on-chain execution

### 5. Code Quality (10%)

- **Clean architecture** — modular, extensible, well-documented
- **Production-ready patterns** — async, type hints, error handling
- **Observability** — audit trail, metrics, structured logging

### How to Maximize Your Score

✅ **Show the full pipeline** — detection → reasoning → execution → notification
✅ **Highlight the AI** — the LLM reasoning step is your differentiator
✅ **Show real numbers** — gas costs, yield improvements, health factors
✅ **Keep it tight** — judges appreciate concise, impactful demos
✅ **Include architecture context** — the final dashboard shows your system design

---

## Troubleshooting

### Rich Not Installed

```bash
pip install rich
```

The demo will fall back to ANSI codes, but output will be less visually appealing.

### Unicode Characters Not Rendering

If you see boxes or question marks instead of emojis/symbols:

```bash
# Set locale to UTF-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

### Demo Too Slow / Too Fast

- Use `--fast` flag for shorter delays
- Edit the `_sleep()` calls in `demo.py` to adjust timing per step

### Terminal Too Small

The demo output is designed for a **minimum terminal width of 100 characters**. Resize your terminal if tables appear truncated:

```bash
# iTerm2: Window → Split Pane → Adjust size
# Windows Terminal: Drag the window edge
# Linux: Right-click terminal → Preferences → Set columns ≥ 120
```

### Script Fails on Import

```bash
# Ensure you're in the project root
cd /opt/sandbox/workspace/defi-sentinel

# Install in development mode
pip install -e .
```

---

## Quick Checklist

- [ ] `pip install -e ".[dev]"` completed
- [ ] Terminal is dark-themed, monospace font, ≥100 columns wide
- [ ] OBS/screen recorder configured (1080p, 30fps, 6000 Kbps)
- [ ] Ran `python scripts/demo.py --fast` for a preview
- [ ] Ran `clear` before the actual recording
- [ ] Recorded the full run (start to final dashboard)
- [ ] Trimmed and exported as MP4
- [ ] Video is 1.5–2 minutes long
- [ ] Added project name and GitHub link in description

---

**Good luck with the hackathon! 🚀**