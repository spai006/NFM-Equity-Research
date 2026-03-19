# 📈 NFM Equity Research Platform (v2)

NFM‑Equity‑Research is a quantitative stock-ranking engine and research-focused equity analysis platform that uses a New Fundamental Model (NFM) combined with LLM‑based reasoning to identify, rank, and continuously monitor the fundamentally strongest companies in the Indian stock market.

The scalable research pipeline evaluates thousands of listed Indian equities (scoring 500+ NSE equities across 10+ weighted fundamental parameters). It features a live state-management system that auto-triggers churn alerts on regime shifts, selects the Top 50 companies, generates explainable investment insights, and dynamically updates the list as business fundamentals evolve.

> ⚠️ **Disclaimer:** This is a research and decision-support system. It does NOT guarantee returns. It aims to maximize probability of strong investments through systematic analysis.

---

## 🚀 Project Evolution (v2 Pivot)

Version 2 introduces a more realistic and scalable design, pivoting from the prototype stage to a robust production-ready framework.

### Why the Pivot?
The pivot was driven by the need for:
- **Low-Latency Execution:** Engineering a low-latency C++ execution core with Shared Memory, Ring Buffers, SIMD vectorisation, and custom Object Pools to handle high-frequency data ingestion with minimal overhead and latency.
- **Live State-Management:** Implementing a live state-management system that auto-triggers churn alerts on regime shifts, mimicking actual institutional workflows.
- **Scalable Research Pipeline:** Ensuring the architecture can analyze thousands of listed Indian equities through automated feature engineering, ranking, and continuous monitoring workflows.

### 📜 Legacy Version 1
All original modules and prototypes have been moved to:
- [`/legacy_v1/`](./legacy_v1/)

These files are retained for historical reference and audit purposes but are formally deprecated in favor of the v2 architecture.

---

## 🎯 Objectives
- **Build a scalable fundamentals-driven equity screening engine**
- **Rank Indian equities** using a weighted NFM model
- **Generate human-readable reasoning** using LLMs
- **Monitor deterioration signals** and trigger early warnings
- **Maintain a dynamic Top 50 list** via automated churn logic
- **Provide transparent and explainable scoring**

---

## 🧠 High-Level Architecture
```text
Market Universe (Thousands of Indian Equities)
        ↓
High-Frequency Data Ingestion (Low-Latency C++ Core)
        ↓
Automated Feature Engineering (10+ Fundamental Parameters)
        ↓
Quantitative Stock-Ranking Engine
        ↓
Top 50 Stock Selection
        ↓
LLM‑Based Explainable Investment Insights
        ↓
Live State-Management & Continuous Monitoring
        ↓
Automated Churn Alerts (Regime Shifts)
```

---

## 📂 Project Structure
```text
NFM-Equity-Research/
│
├── src/
│   ├── data_ingestion/     # Data fetching & loading
│   ├── metrics/            # Fundamental metrics & feature engineering
│   ├── scoring/            # NFM scoring & ranking logic
│   ├── monitoring/         # Alerts & deterioration tracking
│   ├── llm_reasoning/      # Prompting & explanation generation
│   ├── pipeline/           # Pipeline orchestration
│   └── validation/         # Data validation checks
│
├── data/                   # Raw & processed financial data
├── reports/                # Research outputs & Top 50 reports
├── config/                 # Model weights & settings
├── tests/                  # Unit tests
│
├── pipeline_run.py         # Main pipeline entry point
├── README.md               # Original README
├── README_v2.md            # Modernized Pivot README
└── requirements.txt
```

---

## ⚙️ Installation
```bash
git clone https://github.com/your-username/NFM-Equity-Research.git
cd NFM-Equity-Research
pip install -r requirements.txt
```

---

## ▶️ Usage
Run the full pipeline:
```bash
python pipeline_run.py
```
**Pipeline steps:**
1. Data ingestion & cleaning
2. Metric computation
3. NFM scoring & ranking
4. Top 50 selection
5. LLM explanation generation
6. Monitoring & churn updates
7. Report generation

---

## 🔁 Continuous Monitoring Logic
The system tracks critical health signals:
- **Score deterioration**
- **Debt or cash‑flow stress**
- **Profitability decline**
- **Abnormal price/volume signals**

Alerts are triggered immediately when thresholds are breached.

---

## 🔄 Churn Logic
A company may be **removed** if:
- Rank drops below threshold
- Fundamentals deteriorate significantly

A company may be **added** if:
- It rises into top ranks
- Shows consistent fundamental strength

*All churn decisions are explainable and logged.*

---

## 🧪 Testing
```bash
pytest tests/
```
Tests cover metric calculations, scoring logic, and monitoring triggers.

---

## 🛠 Configuration
Core settings (weights, thresholds, API configs) are managed in:
`config/settings.py`

---

## 📌 Future Roadmap
- [ ] Dashboard UI (Streamlit)
- [ ] Historical backtesting module
- [ ] Sector‑aware ranking
- [ ] Risk‑adjusted scoring
- [ ] Advanced anomaly detection

---

## 👥 Contributors
Built as a collaborative quant research project by:
- Somnath
- Anvesh
- Jaju
- Shubham

---

## 📄 Disclaimer
This project is for educational and research purposes only. **Not financial advice.**
