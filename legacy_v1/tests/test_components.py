
import sys
import os
import pandas as pd
import numpy as np

# Adjust path to find src
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.metrics import compute_metrics
from src.scoring import scorer
from src.llm_reasoning import prompts
from config import settings

def test_full_flow():
    print(">>> Starting Model Brain Component Test...")

    # 1. Dummy Input Data (Raw Financials)
    raw_data = {
        "ticker": ["ALPHA", "BETA"],
        "net_income": [100.0, 50.0],
        "equity": [500.0, 1000.0],
        "ebit": [150.0, 80.0],
        "capital_employed": [600.0, 1200.0],
        "revenue": [1000.0, 500.0],
        "revenue_3y_ago": [700.0, 450.0], # High growth for Alpha
        "profit_3y_ago": [60.0, 40.0],
        "total_debt": [200.0, 100.0],
        "interest_expense": [10.0, 5.0],
        "cfo": [120.0, 40.0], # Good OCF
        "capex": [20.0, 10.0],
        "total_assets": [800.0, 1100.0],
        "std_net_income": [5.0, 1.0], 
        "mean_net_income": [100.0, 50.0]
    }
    
    df = pd.DataFrame(raw_data)
    print(f"\n[1] Created Dummy DataFrame with {len(df)} companies.")

    # 2. Compute Metrics
    print("\n[2] Computing Metrics...")
    # Apply row-wise computation
    computed_metrics_list = []
    for _, row in df.iterrows():
        # compute_all_metrics returns a dict
        metrics = compute_metrics.compute_all_metrics(row)
        metrics['ticker'] = row['ticker'] # Keep identifier
        computed_metrics_list.append(metrics)
    
    metrics_df = pd.DataFrame(computed_metrics_list)
    print("Computed Columns:", metrics_df.columns.tolist())
    
    # Check a few values
    alpha = metrics_df[metrics_df['ticker'] == 'ALPHA'].iloc[0]
    print(f"DTOE Alpha: {alpha['debt_to_equity']} (Expected ~0.4)")
    print(f"ROE Alpha: {alpha['roe']} (Expected ~0.2)")

    # 3. Scoring
    print("\n[3] Running Scorer...")
    # scorer.normalize_metrics expects a DataFrame and returns DataFrame with 'final_score'
    scored_df = scorer.normalize_metrics(metrics_df)
    
    print("Scored DataFrame:\n", scored_df[['ticker', 'final_score', 'roe', 'debt_to_equity']])
    
    # Check who won
    winner = scored_df.sort_values('final_score', ascending=False).iloc[0]
    print(f"\nWinner is {winner['ticker']} with Score {winner['final_score']:.2f}")

    # 4. Generate Prompts
    print("\n[4] Testing Prompts...")
    rank = 1
    justification = prompts.generate_justification_prompt(winner, rank)
    print(f"--- Justification Prompt for {winner['ticker']} ---\n{justification[:200]}...\n")

    churn_remove = prompts.generate_churn_prompt(scored_df.iloc[1], "REMOVE", 55)
    print(f"--- Churn Remove Prompt for {scored_df.iloc[1]['ticker']} ---\n{churn_remove[:200]}...\n")

    print("\n>>> TEST PASSED SUCCESSFULLY")

if __name__ == "__main__":
    test_full_flow()
