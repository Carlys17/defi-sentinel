# 🎥 Shot List — DeFi Sentinel Demo Recording

> **Total shots:** 10
> **Estimated recording time:** 15-20 minutes
> **Format:** 1080p, 30fps, MP4

---

## Pre-Recording Setup

```bash
# 1. Navigate to project root
cd /root/defi-sentinel

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Clear terminal
clear

# 4. Resize terminal: minimum 120 columns x 40 rows
#    (required so tables don't truncate)

# 5. Verify .env exists
ls -la .env
```

### ⚠️ Demo Risks
- `.env` is present ✅
- Wallet has ~0.1 BASE balance on Base Sepolia ✅
- MCP session initialization tested ✅
- **Risk:** If KeeperHub MCP server is down, simulation may fail → fallback: show existing transaction links
- **Risk:** If `python3 scripts/hackathon_demo.py` fails due to missing keys, use `python3 scripts/demo.py --fast` as fallback

---

## Shot 1: Hook — Logo & Title (0:00-0:15)

**Command:**
```bash
python3 -c "
print('''
██████╗ ██████╗  █████╗  ██████╗██╗  ██╗███████╗██████╗
██╔══██╗██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
██████╔╝██████╔╝███████║██║     █████╔╝ █████╗  ██████╔╝
██╔═══╝ ██╔══██╗██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
██║     ██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
''')
print('DeFi Sentinel - Autonomous AI Agent for DeFi Portfolio Management')
print('Powered by KeeperHub Execution Layer')
"
```

**Duration:** 10 seconds
**Note:** Hold frame, no scrolling

---

## Shot 2: Problem Statement (0:15-0:40)

**Command:**
```bash
cat << 'EOF'
PROBLEM: Most agent hackathons reward reasoning.
The harder problem is what happens next.

Agents can detect and decide, but they all hit the same wall:
- Failed transactions
- Gas spikes
- MEV extraction
- No observability
- No guarantees

KEEPERHUB: The last mile between decision and execution.
EOF
```

**Duration:** 15 seconds

---

## Shot 3: Architecture (0:40-1:20)

**Command:**
```bash
grep -A 40 "Architecture" README.md | head -45
```

**Duration:** 20 seconds
**Note:** Zoom into KeeperHub MCP Client section

---

## Shot 4: KeeperHub Demo — Initialize (1:20-1:35)

**Command:**
```bash
python3 scripts/hackathon_demo.py --simulate 2>&1 | head -30
```

**Duration:** 15 seconds
**Note:** Highlight "MCP session initialized"

---

## Shot 5: KeeperHub Demo — Wallet & Actions (1:35-1:50)

**Command:**
```bash
python3 scripts/hackathon_demo.py --simulate 2>&1 | sed -n '30,60p'
```

**Duration:** 15 seconds
**Note:** Highlight "Wallet Integration" and "Action Discovery"

---

## Shot 6: KeeperHub Demo — Execution (1:50-2:10)

**Command:**
```bash
python3 scripts/hackathon_demo.py --simulate 2>&1 | grep -A 10 "TRANSACTION RESULT"
```

**Duration:** 20 seconds
**Note:** Zoom into "Status: COMPLETED"

---

## Shot 7: Transaction Proof #1 (2:10-2:25)

**Command:**
```bash
echo "Transaction #1: 0xc244ad7e2ea2235161f51813524c330f53ad8214f9ba69c698cda127483ff429"
echo "Status: COMPLETED"
echo "Explorer: https://sepolia.basescan.org/tx/0xc244ad7e2ea2235161f51813524c330f53ad8214f9ba69c698cda127483ff429"
```

**Duration:** 15 seconds
**Note:** If possible, open browser and screenshot transaction page

---

## Shot 8: Transaction Proof #2 (2:25-2:40)

**Command:**
```bash
echo "Transaction #2: 0x9a9668a32a18637c86d5484bcf57820fa282bed9f841337f5c0c3889d5c5ba97"
echo "Status: COMPLETED"
echo "Explorer: https://sepolia.basescan.org/tx/0x9a9668a32a18637c86d5484bcf57820fa282bed9f841337f5c0c3889d5c5ba97"
```

**Duration:** 15 seconds

---

## Shot 9: Safety & Observability (2:40-2:55)

**Command:**
```bash
echo "=== AUDIT TRAIL ==="
cat logs/audit.jsonl 2>/dev/null | tail -3 | python3 -m json.tool 2>/dev/null || echo "Audit logs available in logs/audit.jsonl"

echo ""
echo "=== PROMETHEUS METRICS ==="
echo "• monitoring_cycles_total"
echo "• decisions_made_total"
echo "• transactions_executed_total"
echo "• portfolio_value_usd"
echo "• errors_total"
```

**Duration:** 15 seconds

---

## Shot 10: Closing (3:10-3:30)

**Command:**
```bash
cat << 'EOF'
========================================
  DeFi Sentinel
  Autonomous AI Agent for DeFi
  Powered by KeeperHub
========================================

GitHub: https://github.com/Carlys17/defi-sentinel
Tx #1:  https://sepolia.basescan.org/tx/0xc244ad7e2ea2235161f51813524c330f53ad8214f9ba69c698cda127483ff429
Tx #2:  https://sepolia.basescan.org/tx/0x9a9668a32a18637c86d5484bcf57820fa282bed9f841337f5c0c3889d5c5ba97

Hackathon: DoraHacks - Agents Onchain
========================================
EOF
```

**Duration:** 20 seconds

---

## Equipment Checklist

- [ ] Terminal: Dark theme, monospace font (JetBrains Mono/Fira Code), 120x40
- [ ] Recorder: OBS Studio (1080p, 30fps, 6000 Kbps)
- [ ] Microphone: USB mic for separate voiceover
- [ ] Browser: Chrome/Firefox for BaseScan
- [ ] Editor: DaVinci Resolve / Premiere for editing

## Recording Tips

1. **Practice 2-3 times** with `--fast` mode before serious recording
2. **Record voiceover separately** — easier to sync in editing
3. **Add cursor highlight** — guide viewer attention
4. **Zoom-in** when showing transaction hash
5. **Speed up** slow sections (e.g., loading)