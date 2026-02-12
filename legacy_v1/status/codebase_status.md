# Codebase Walkthrough & Status Report

## Configuration (`config/`)
- **`settings.py`**: [Implemented] Central configuration. Defines file paths, NSE market suffix (`.NS`), field mappings for Yahoo Finance, and the **Scoring Weights** for the NFM model (e.g., ROE=15.0, Debt/Equity=5.0).

## Source Code (`src/`)

### Data Ingestion (`src/data_ingestion/`)
- **`fetcher.py`**: [Implemented] Uses `yfinance` to fetch Balance Sheet, P&L, and Cash Flow for a given ticker. Returns raw DataFrames.
- **`processor.py`**: [Implemented] Cleans raw data. Extracts key fields using the mapping from settings. Handles edge cases like missing liabilities (fallback to Equity+Debt) and ensures positive values for Capex where needed. Returns a flat dictionary.

### Metrics (`src/metrics/`)
- **`compute_metrics.py`**: [Implemented] Core financial logic. Contains pure functions for computing ROE, ROCE, CAGRs, Leverage ratios, and Efficiency metrics. Handles division by zero safely.

### Scoring (`src/scoring/`)
- **`scorer.py`**: [Implemented] Implements the NFM Ranking Model. 
    - Normalizes raw metrics to 0-1 percentile ranks.
    - Inverts logic for "Lower is Better" metrics (e.g., Debt/Equity).
    - Computes weighted sum based on `settings.SCORING_WEIGHTS`.

### Monitoring (`src/monitoring/`)
- **`alerts.py`**: [Implemented] Logic to detect significant changes (Score drops >15%, Debt Spikes, Cash Flow collapse).
- **`churn.py`**: [Implemented] Logic to decide if a company stays in Top 50. Currently relies on strict Rank threshold (>50 = Remove).
- **`test_monitoring.py`**: [Test] Script to verify monitoring logic independently.

### LLM Reasoning (`src/llm_reasoning/`)
- **`prompts.py`**: [Implemented] Template generators for "Justification" (Why this stock?) and "Churn" (Why remove this stock?) prompts.
- **`prompt_template.txt`**: [Implemented] Text file template for the explanation engine.
- **`generate_explanations.py`**: [Partial] **Action Item**. Currently uses a **Simulated** rule-based response generator. Needs to be updated to call a real LLM API (OpenAI/Gemini).
- **`generate_charts.py`**: [Implemented] Generates a static bar chart of the Top 50 scores and saves it to `reports/assets/`.

### Pipeline Orchestration (`src/pipeline/`)
- **`run_data_pipeline.py`**: [Implemented] The heavy lifter. Iterates through all ~6000 NSE tickers, fetches data, processes it, computes metrics, and saves to `data/processed/features.csv`. Supports resumability.
- **`run_scoring.py`**: [Implemented] Loads processed data, runs the Scorer, generates the Top 50 list, and saves separate history snapshots (`data/reports/history/`).
- **`run_monitoring.py`**: [Implemented] Compares today's Top 50 vs yesterday's. Generates `daily_brief.md` highlighting new entrants and significant movers.

## Main Entry Point
- **`pipeline_run.py`**: [Implemented] Master script. Runs Ingestion -> Scoring -> Monitoring in sequence.

---
## Status Summary
- **Core Logic**: ✅ Complete & Verified.
- **Data Pipeline**: ✅ Complete (Verified with Dry Run).
- **LLM Integration**: ⚠️ **Pending**. The logic exists but uses a mock generator.
- **Reporting**: ✅ Basic CSV and Markdown reporting is active.

## Next Recommendation
Enable real LLM generation in `src/llm_reasoning/generate_explanations.py` by integrating an API client.
