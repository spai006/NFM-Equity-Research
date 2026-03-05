NFM-Equity-Research is a research-focused equity analysis platform that uses a New Fundamental Model (NFM) combined with LLM-based reasoning to identify, rank, and continuously monitor the fundamentally strongest companies in the Indian stock market.

The system evaluates ~6,000 listed Indian companies using multi-factor fundamental data, selects the Top 50 companies, generates explainable research justifications, and dynamically updates the list as business fundamentals evolve.

This project is designed to emulate and potentially outperform high-performance LLM-driven equity research systems (≈50% XIRR benchmarks) through transparent scoring, continuous monitoring, and automated churn logic.

## Objectives

- **Build a scalable fundamentals-driven equity screening engine**
- **Rank Indian equities** using a weighted New Fundamental Model
- **Generate human-readable reasoning** for stock selection using LLMs
- **Monitor deterioration signals** and trigger early warnings
- **Maintain a dynamic Top 50 list** via automated churn decisions

## High-Level Architecture

- Market Universe (~6,000 Stocks)
- Fundamental Data Ingestion
- Feature Engineering (40+ Parameters)
- NFM Weighted Scoring Engine  
- Top 50 Stock Selection   
- LLM-Based Research & Explanation    
- Continuous Monitoring & Alerts       
- Churn (Add / Remove Companies)

## Project Structure

```
NFM-Equity-Research/
│
├── src/
│   ├── data_ingestion/       # Data fetching and loading
│   ├── metrics/              # Feature engineering & fundamental metrics
│   ├── scoring/              # NFM scoring & ranking models
│   ├── monitoring/           # Continuous tracking & alerts
│   ├── llm_reasoning/        # Prompting & explanation generation
│   ├── pipeline/             # Pipeline orchestration components
│   └── validation/           # Data validation logic
│
├── data/                     # Raw & processed financial data
├── reports/                  # Company-level research outputs
├── config/                   # Parameter configs & weights
├── tests/                    # Unit tests
├── pipeline_run.py           # Main entry point script
├── README.md
└── requirements.txt
```

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/NFM-Equity-Research.git
    cd NFM-Equity-Research
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To run the full automated analysis pipeline, execute the main script:

```bash
python pipeline_run.py
```

This pipeline performs the following steps sequentially:
1.  **Data Ingestion & Processing:** Fetches latest market data and computes fundamental metrics.
2.  **Scoring & Ranking:** Applies the NFM model to score stocks and select the Top 50.
3.  **Monitoring & Reporting:** Generates a daily brief and updates monitoring logs (e.g., churn, alerts).

## Configuration

Core configuration settings, including path definitions, model weights, and API keys (if applicable), are located in `config/settings.py`.
