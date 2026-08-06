# 🎬 Video Script — DeFi Sentinel Hackathon Demo

> **Durasi target:** 3-4 menit  
> **Bahasa:** Indonesia  
> **Tempo:** Cepat, fokus ke bukti eksekusi onchain nyata

---

## Segmen 1: Hook (0:00-0:15)

**Visual:** Logo DeFi Sentinel + ASCII art di terminal

> "DeFi Sentinel — AI agent otonom yang tidak hanya berpikir, tapi benar-benar mengeksekusi transaksi onchain. Ini bukan mockup. Ini bukti nyata."

---

## Segmen 2: Problem (0:15-0:40)

**Visual:** Screenshot portfolio DeFi dengan health factor rendah

> "Problemnya begini: sebagian besar agent hackathon cuma bisa reasoning — agent yang memutuskan sesuatu yang pintar. Tapi masalah sesungguhnya ada di langkah berikutnya. Agent bisa detect dan decide, tapi semua macet di tembok yang sama saat harus move value onchain. Failed transactions, gas spikes, MEV, no observability, no guarantees. KeeperHub adalah solusi — the last mile antara apa yang agent putuskan dan transaksi yang benar-benar jalan onchain."

---

## Segmen 3: Solusi & Arsitektur (0:40-1:20)

**Visual:** Diagram arsitektur dari README

> "DeFi Sentinel dibangun di atas KeeperHub sebagai execution layer. Arsitekturnya begini: LLM Engine — OpenAI atau Anthropic — melakukan reasoning dan menghasilkan structured JSON output. Strategy Engine punya tiga strategi: Liquidation Shield yang monitor health factor dan auto eksekusi collateral atau repay, Yield Optimizer yang scan APR cross-protocol dan realokasi capital, dan Portfolio Rebalancer yang maintain target allocation. Semua keputusan dari agent dieksekusi lewat KeeperHub MCP Client — workflow execution, DeFi protocol actions, direct transfers, dan contract calls. Simulation-first: setiap transaksi disimulasikan dulu sebelum benar-benar jalan."

---

## Segmen 4: Demo Integrasi KeeperHub (1:20-2:10)

**Visual:** Live terminal — jalankan `python3 scripts/hackathon_demo.py --simulate`

> "Sekarang kita lihat langsung di terminal. Saya jalankan demo script. Langkah pertama: MCP session initialized — koneksi ke KeeperHub server via JSON-RPC 2.0. Langkah kedua: wallet integration verified — wallet 0x749B...terhubung. Langkah ketiga: action schemas loaded — Aave V3, Compound, Morpho, Yearn, Uniswap, CowSwap semua tersedia. Langkah keempat: simulation passed — transfer 0.001 BASE disimulasikan, tidak ada revert. Langkah kelima: real execution — dan ini yang penting — transaksi benar-benar dieksekusi onchain via KeeperHub. Status: COMPLETED."

---

## Segmen 5: Bukti Transaksi Onchain (2:10-2:40)

**Visual:** Buka BaseScan explorer untuk 2 transaksi

> "Ini bukan simulasi. Ini transaksi nyata di Base Sepolia. Transaksi pertama: 0xc244... — completed. Transaksi kedua: 0x9a96... — juga completed. Dua transaksi yang dieksekusi langsung oleh agent lewat KeeperHub MCP. Bisa dicek langsung di BaseScan. Ini yang diminta hackathon: working transactions, not mockups."

---

## Segmen 6: Safety & Observability (2:40-3:10)

**Visual:** Tampilkan audit trail log & metrics

> "Setiap aksi agent dicatat di audit trail: trigger, simulation result, submitted transaction, gas used, outcome, timestamp. Idempotency keys untuk retry-safe execution. Smart gas estimation yang adaptif ke network congestion. Prometheus metrics untuk observability. Semua ini memastikan agent tidak cuma bisa jalan, tapi jalan dengan aman dan bisa di-audit."

---

## Segmen 7: Closing + CTA (3:10-3:30)

**Visual:** GitHub repo link + transaction links

> "DeFi Sentinel — autonomous AI agent for DeFi portfolio management, powered by KeeperHub execution layer. GitHub: github.com/Carlys17/defi-sentinel. Dua transaksi verified on Base Sepolia. Submit untuk DoraHacks Agents Onchain hackathon. Terima kasih!"

---

## Catatan Produksi

- **Voiceover:** Rekam terpisah, sync dengan video di post-production
- **BGM:** Instrumental lo-fi/ambient (volume rendah)
- **Subtitle:** Wajib (bahasa Indonesia + English)
- **Zoom-in:** Saat menunjukkan transaction hash di terminal
- **Highlight:** Gunakan cursor/mouse pointer untuk arahkan perhatian viewer