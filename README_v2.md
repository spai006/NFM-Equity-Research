# 📈 NFM Equity Research Platform (v2)

NFM‑Equity‑Research is a real-time equity ranking system for NSE stocks. It uses a **hybrid Python–C++ pipeline** where Python fetches live market data and pre-cached fundamental factors, streams them into a shared memory ring buffer, and a C++ consumer applies weighted scoring to maintain a continuously updated equity ranking.

> ⚠️ **Disclaimer:** This is a research and learning project. It does NOT constitute financial advice or guarantee returns.

---

## 🚀 Project Evolution (v2 Pivot)

Version 2 introduces a fundamentally different architecture, pivoting from the batch prototype (v1) to a real-time streaming pipeline.

### Why the Pivot?
The pivot was driven by the need for:

- **Hybrid Performance & Low-Latency Execution:** Python handles data ingestion and factor computation; a C++ execution core reads from a shared memory ring buffer and performs weighted scoring with microsecond-level processing latency per record.
- **Real-Time Streaming:** Instead of running a batch job once a day, the producer streams live price and volume data at a 5-second tick rate, continuously updating the equity state.
- **IPC via Memory-Mapped Ring Buffer:** Python and C++ communicate through a memory-mapped file (`market_state.bin`) with a lock-free 1024-record ring buffer using atomic head/tail synchronization — eliminating serialization overhead.

### 📜 Legacy Version 1
All original batch pipeline modules have been moved to:
- [`/legacy_v1/`](./legacy_v1/)

These files are retained for reference but are formally deprecated in favour of the v2 architecture.

---

## 🎯 Objectives

- **Rank NSE equities in real time** using a weighted multi-factor model
- **Stream live market data** into a C++ scoring engine via shared memory IPC
- **Cache fundamental factors daily** to avoid per-tick API overhead
- **Track portfolio constituent changes** between runs
- **Automate the pipeline** via GitHub Actions on weekdays

---

## 🧠 High-Level Architecture

```text
NSE Universe (50 Equities, stable ticker → stock_id mapping)
        ↓
Python Producer
├── Fetches live price + volume (yfinance, every 5s)
└── Loads pre-cached fundamentals (fundamentals_cache.json)
        ↓
Memory-Mapped Ring Buffer IPC
(market_state.bin | 1024 records | atomic head/tail)
        ↓
C++ Consumer
├── Drains ring buffer (tail chases head)
├── Applies weighted dot-product across 10 factors
├── Updates live equity state map (stock_id → score)
└── Outputs Top 10 every 500 updates
        ↓
Churn Monitor (Python)
└── Set-difference between consecutive Top 50 snapshots
    Alerts if portfolio turnover > 20%
```

---

## 🧬 Factors

Each stock record carries **10 factors** written by the Python producer:

| Index | Factor | Type |
|-------|--------|------|
| 0 | Live Price | Real-time (yfinance) |
| 1 | Live Volume (scaled) | Real-time (yfinance) |
| 2 | P/E Ratio | Cached fundamental |
| 3 | PEG Ratio | Cached fundamental |
| 4 | Revenue Growth (1Y) | Cached fundamental |
| 5 | EPS Growth | Cached fundamental |
| 6 | Return on Equity (ROE) | Cached fundamental |
| 7 | Return on Capital Employed (ROCE) | Cached fundamental |
| 8 | FCF / Net Profit | Cached fundamental |
| 9 | Debt / Equity | Cached fundamental |

Fundamental factors are pre-computed once daily by `daily_fundamental_cacher.py` and loaded from `data/fundamentals_cache.json` at runtime to eliminate per-tick API calls.

---

## ⚙️ IPC Design

Python and C++ share data through a **memory-mapped file** (`market_state.bin`).

```
SharedBlock {
    head : uint32          // Python increments after each write
    tail : uint32          // C++ increments after each read
    records : Record[1024] // ring buffer
}

Record {
    stock_id : int32
    factors  : double[10]
}
```

- `#pragma pack(1)` ensures Python (`ctypes`) and C++ share identical byte layout with no padding
- `head` and `tail` implement a **lock-free ring buffer**: Python waits when the buffer is full, C++ waits when it is empty
- C++ measures end-to-end execution latency in **microseconds**

---

## 📂 Project Structure

```text
NFM-Equity-Research/
│
├── producer.py                        # Python: live data fetch + ring buffer write
├── main.cpp                           # C++: ring buffer read + weighted scoring
├── shared_memory.h                    # Shared struct layout (Record, SharedBlock)
├── pipeline_run.py                    # Orchestrator: compile C++, run producer + churn
│
├── data/
│   ├── universe_master.csv            # Stable ticker → stock_id mapping
│   └── fundamentals_cache.json        # Pre-computed daily fundamental factors
│
├── src/
│   ├── data_ingestion/
│   │   ├── universe.py                # Universe loader (ticker ↔ stock_id)
│   │   └── build_universe.py
│   ├── metrics/factors/
│   │   └── core_factors.py            # Fundamental + momentum factor computation
│   ├── monitoring/
│   │   └── churn.py                   # Portfolio turnover tracker
│   └── pipeline/
│       ├── factor_engine.py           # Batch factor computation + IPC write (alt mode)
│       └── daily_fundamental_cacher.py
│
├── .github/workflows/daily_run.yml    # GitHub Actions: automated weekday runs
├── README.md
├── README_v2.md
└── legacy_v1/                         # Archived v1 batch pipeline
```

---

## ⚙️ Installation

```bash
git clone https://github.com/spai006/NFM-Equity-Research.git
cd NFM-Equity-Research
pip install -r requirements.txt
```

---

## ▶️ Usage

**Step 1 — Cache fundamentals (run once daily or on first run):**
```bash
python src/pipeline/daily_fundamental_cacher.py
```

**Step 2 — Run the full pipeline:**
```bash
python pipeline_run.py
```

Pipeline steps:
1. Compile `main.cpp` (skipped if already up to date)
2. Start Python producer (live data fetch + ring buffer write)
3. Start C++ consumer (ring buffer read + weighted scoring + Top 10 output)
4. Run churn monitor (portfolio turnover between runs)

**Stop the producer:** `Ctrl+C`

---

## 🔄 Churn Monitor

After each run, `churn.py` compares the current Top 50 against the previous run using **set difference**:

- Logs new entrants (stocks that entered Top 50)
- Logs dropouts (stocks that left Top 50)
- Alerts if portfolio turnover exceeds **20%**

This is a simple state-tracking mechanism between consecutive pipeline runs.

---

## 📌 Current Limitations

- Universe is fixed at **50 equities** (ring buffer struct capacity)
- Factor weights are manually set, not learned or backtested
- No historical performance evaluation or backtesting
- Live data only available during NSE market hours

---

## 🔭 Future Roadmap

- [ ] Expand universe beyond 50 stocks (dynamic allocation)
- [ ] Cross-sectional Z-score normalization in the live pipeline
- [ ] Add momentum factors (6M/12M returns, price-to-200DMA) to live stream
- [ ] Backtest ranking quality against NSE index returns
- [ ] Factor weight optimization
- [ ] Dashboard UI (Streamlit)
- [ ] Sector-aware ranking

---

## 👥 Contributors

Built as a collaborative quant research project by:
- Somnath
- Anvesh
- Jaju

---

## 📄 Disclaimer

This project is for educational and research purposes only. **Not financial advice.**
