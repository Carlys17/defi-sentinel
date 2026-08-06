# 🎥 Shot List — DeFi Sentinel Demo Recording

> **Total shots:** 12  
> **Estimasi waktu rekam:** 15-20 menit  
> **Format:** 1080p, 30fps, MP4

---

## Setup Sebelum Rekam

```bash
# 1. Pastikan di directory yang benar
cd /root/defi-sentinel

# 2. Pastikan dependencies terinstall
pip install -e ".[dev]"

# 3. Clear terminal
clear

# 4. Resize terminal: minimal 120 kolom x 40 baris
#    (penting agar tabel tidak terpotong)

# 5. Verifikasi .env sudah ada
ls -la .env
```

### ⚠️ Risiko Saat Demo
- `.env` sudah terisi dengan KeeperHub API key ✅
- Wallet punya balance ~0.1 BASE di Base Sepolia ✅
- MCP session bisa initialize (sudah ditest) ✅
- **Risiko:** Jika MCP server down, simulation gagal → punya fallback: tunjukkan transaksi yang sudah ada

---

## Shot 1: Hook — Logo & Title (0:00-0:15)

**Command:**
```bash
# Tampilkan ASCII art
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

**Durasi rekam:** 10 detik  
**Catatan:** Tahan layar, jangan scroll

---

## Shot 2: Problem Statement (0:15-0:40)

**Command:**
```bash
# Tampilkan teks problem statement
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

**Durasi rekam:** 15 detik

---

## Shot 3: Arsitektur (0:40-1:20)

**Command:**
```bash
# Tampilkan diagram arsitektur dari README
grep -A 40 "Architecture" README.md | head -45
```

**Durasi rekam:** 20 detik  
**Catatan:** Zoom-in ke bagian KeeperHub MCP Client

---

## Shot 4: Demo KeeperHub — Initialize (1:20-1:35)

**Command:**
```bash
# Jalankan demo script (simulasi mode)
python3 scripts/hackathon_demo.py --simulate 2>&1 | head -30
```

**Durasi rekam:** 15 detik  
**Catatan:** Highlight bagian "MCP session initialized"

---

## Shot 5: Demo KeeperHub — Wallet & Actions (1:35-1:50)

**Command:**
```bash
# Lanjutkan output demo
python3 scripts/hackathon_demo.py --simulate 2>&1 | sed -n '30,60p'
```

**Durasi rekam:** 15 detik  
**Catatan:** Highlight "Wallet Integration" dan "Action Discovery"

---

## Shot 6: Demo KeeperHub — Execution (1:50-2:10)

**Command:**
```bash
# Tampilkan hasil eksekusi
python3 scripts/hackathon_demo.py --simulate 2>&1 | grep -A 10 "TRANSACTION RESULT"
```

**Durasi rekam:** 20 detik  
**Catatan:** Zoom-in ke "Status: COMPLETED"

---

## Shot 7: Bukti Transaksi #1 (2:10-2:25)

**Command:**
```bash
# Buka browser ke BaseScan
# URL: https://sepolia.basescan.org/tx/0xc244ad7e2ea2235161f51813524c330f53ad8214f9ba69c698cda127483ff429

# Atau tampilkan di terminal:
echo "Transaction #1: 0xc244ad7e2ea2235161f51813524c330f53ad8214f9ba69c698cda127483ff429"
echo "Status: COMPLETED"
echo "Explorer: https://sepolia.basescan.org/tx/0xc244ad7e2ea2235161f51813524c330f53ad8214f9ba69c698cda127483ff429"
```

**Durasi rekam:** 15 detik  
**Catatan:** Jika bisa, buka browser dan screenshot halaman transaksi

---

## Shot 8: Bukti Transaksi #2 (2:25-2:40)

**Command:**
```bash
echo "Transaction #2: 0x9a9668a32a18637c86d5484bcf57820fa282bed9f841337f5c0c3889d5c5ba97"
echo "Status: COMPLETED"
echo "Explorer: https://sepolia.basescan.org/tx/0x9a9668a32a18637c86d5484bcf57820fa282bed9f841337f5c0c3889d5c5ba97"
```

**Durasi rekam:** 15 detik

---

## Shot 9: Safety & Observability (2:40-2:55)

**Command:**
```bash
# Tampilkan audit trail
echo "=== AUDIT TRAIL ==="
cat logs/audit.jsonl 2>/dev/null | tail -3 | python3 -m json.tool 2>/dev/null || echo "Audit logs available in logs/audit.jsonl"

# Tampilkan metrics
echo ""
echo "=== PROMETHEUS METRICS ==="
echo "• monitoring_cycles_total"
echo "• decisions_made_total"
echo "• transactions_executed_total"
echo "• portfolio_value_usd"
echo "• errors_total"
```

**Durasi rekam:** 15 detik

---

## Shot 10: Demo Full Run (2:55-3:10)

**Command:**
```bash
# Jalankan full demo
python3 scripts/hackathon_demo.py --simulate 2>&1 | tail -30
```

**Durasi rekam:** 15 detik  
**Catatan:** Highlight summary table dengan semua PASS

---

## Shot 11: Closing (3:10-3:20)

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

**Durasi rekam:** 10 detik

---

## Shot 12: B-Roll — Codebase (opsional)

**Command:**
```bash
# Tampilkan struktur project
tree -L 2 --charset ascii

# Tampilkan LOC stats
echo ""
echo "Total: ~3,548 LOC | 149 functions | 31 classes"
echo "Languages: Python 100%"
echo "Test coverage: helpers, settings, keeperhub client"
```

**Durasi rekam:** 10 detik  
**Catatan:** B-roll untuk transisi antar segmen

---

## Checklist Peralatan

- [ ] Terminal: Dark theme, monospace font (JetBrains Mono/Fira Code), 120x40
- [ ] Recorder: OBS Studio (1080p, 30fps, 6000 Kbps)
- [ ] Microphone: USB mic untuk voiceover terpisah
- [ ] Browser: Chrome/Firefox untuk buka BaseScan
- [ ] Editor: DaVinci Resolve / Premiere untuk editing

## Tips Rekam

1. **Latih 2-3x** dengan `--fast` mode sebelum rekam serius
2. **Rekam voiceover terpisah** — lebih mudah sync di editing
3. **Tambah cursor highlight** — arahkan perhatian viewer
4. **Zoom-in** saat menunjukkan transaction hash
5. **Speed up** bagian yang terlalu lambat (misal: loading)