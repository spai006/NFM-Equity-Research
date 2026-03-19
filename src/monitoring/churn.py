import pandas as pd
from pathlib import Path
import shutil

REPORTS_DIR = Path("reports")
CURRENT_CSV = REPORTS_DIR / "top50.csv"
PREVIOUS_CSV = REPORTS_DIR / "top50_previous.csv"

def compute_churn():
    if not CURRENT_CSV.exists():
        print("Error: No current top50.csv found. Please run the C++ execution core first.")
        return

    # If first run, establish the baseline state
    if not PREVIOUS_CSV.exists():
        print("--- 📡 NFM STATE-MANAGEMENT INITIALIZED ---")
        shutil.copy(CURRENT_CSV, PREVIOUS_CSV)
        print("Baseline market state saved to disk.")
        print("Run the pipeline again tomorrow to compute temporal churn.")
        return

    # Read current and previous states
    df_current = pd.read_csv(CURRENT_CSV)
    df_previous = pd.read_csv(PREVIOUS_CSV)

    current_tickers = set(df_current['ticker'])
    previous_tickers = set(df_previous['ticker'])

    # Compute set differences (new elements that are entirely new to the Top 50)
    new_entrants = current_tickers - previous_tickers
    dropouts = previous_tickers - current_tickers

    # Turnover = new constituents / total portfolio size
    turnover = len(new_entrants) / 50.0

    print("--- 📡 NFM TEMPORAL STATE TRACKER ---")
    print(f"CHURN = {turnover:.2f} ({int(turnover * 100)}% Portfolio Turnover)")
    
    if turnover > 0.0:
        print("\n[+] REGIME SHIFT - NEW ENTRANTS:")
        for t in new_entrants:
            rank = df_current[df_current['ticker'] == t]['rank'].values[0]
            print(f"    - {t} (Surged to Rank {rank})")
            
        print("\n[-] DROPPED FROM TOP 50:")
        for t in dropouts:
            print(f"    - {t}")

    # Resume-Critical Feature: Regime Shift Alerts
    if turnover >= 0.20:
        print("\n🚨 STRATEGY ALERT: Regime shift detected (>20% churn). Auto-rebalance recommended.")
    else:
        print("\n✅ Regime stable. No structural market shifts detected.")

    # Save today's state as the baseline for tomorrow's run
    shutil.copy(CURRENT_CSV, PREVIOUS_CSV)

if __name__ == "__main__":
    compute_churn()
