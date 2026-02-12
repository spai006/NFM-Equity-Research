
import pandas as pd
import os
import glob
import sys

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.monitoring import churn, alerts
from src.llm_reasoning import generate_explanations
from config import settings
import json

def get_latest_two_snapshots(report_dir):
    """
    Finds the two most recent CSV files in report_dir.
    Returns (latest_file, previous_file).
    """
    files = glob.glob(os.path.join(report_dir, 'top_50_*.csv'))
    # Sort by filename (Date string YYYY-MM-DD handles alphabetic sort correctly)
    files.sort(reverse=True)
    
    if len(files) < 2:
        return files[0] if files else None, None
    return files[0], files[1]

def generate_daily_brief():
    """
    Compares the latest two snapshots and generates a Churn/Trend report.
    """
    history_dir = os.path.join(settings.DATA_DIR, 'reports', 'history')
    latest_file, prev_file = get_latest_two_snapshots(history_dir)
    
    if not latest_file:
        print("No history files found.")
        return
        
    print(f"Comparing Latest ({os.path.basename(latest_file)}) vs Previous ({os.path.basename(prev_file) if prev_file else 'None'})")
    
    df_curr = pd.read_csv(latest_file)
    curr_tickers = set(df_curr['ticker'])
    
    report_lines = []
    report_lines.append("# Daily NFM Model Brief")
    report_lines.append(f"Date: {os.path.basename(latest_file).replace('top_50_', '').replace('.csv', '')}\n")

    # --- INTEGRATION: Generate Explanations ---
    print(">>> Generating AI Explanations for the latest snapshot...")
    prompt_path = os.path.join(settings.BASE_DIR, 'src', 'llm_reasoning', 'prompt_template.txt')
    output_path = os.path.join(settings.DATA_DIR, 'reports', 'llm_explanations.json')
    
    try:
        generate_explanations.generate_explanations(latest_file, prompt_path, output_path)
    except Exception as e:
        print(f"Warning: AI Explanation Generation Failed: {e}")
    
    # Load Explanations for Lookup
    explanations_map = {}
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r') as f:
                data = json.load(f)
                for item in data:
                    explanations_map[item['ticker']] = item.get('explanation', '')
        except Exception as e:
            print(f"Warning: Could not load explanations: {e}")

    # Helper to extract Verdict
    def get_verdict(ticker):
        text = explanations_map.get(ticker, "")
        if "4. Overall Verdict" in text:
            return text.split("4. Overall Verdict")[1].strip().split('\n')[0]
        return "No AI verdict available."
    
    if prev_file:
        df_prev = pd.read_csv(prev_file)
        prev_tickers = set(df_prev['ticker'])
        
        # 1. Churn Analysis
        new_entrants = curr_tickers - prev_tickers
        dropped_tickers = prev_tickers - curr_tickers
        
        if new_entrants:
            report_lines.append("## 🟢 New Entrants (Added to Top 50)")
            for t in new_entrants:
                row = df_curr[df_curr['ticker'] == t].iloc[0]
                rank = list(df_curr['ticker']).index(t) + 1
                decision = churn.decide_churn(rank, []) # No alerts for new entry usually
                verdict = get_verdict(t)
                report_lines.append(f"- **{t}** (Rank #{rank}): {decision['reason']}")
                report_lines.append(f"  > *AI Verdict*: {verdict}")
            report_lines.append("")
                
        if dropped_tickers:
            report_lines.append("## 🔴 Dropped Companies (Exited Top 50)")
            for t in dropped_tickers:
                try:
                    row = df_prev[df_prev['ticker'] == t].iloc[0]
                    prev_rank = list(df_prev['ticker']).index(t) + 1
                except IndexError:
                    row = {}
                    prev_rank = "N/A"
                    
                report_lines.append(f"- **{t}** (Prev Rank #{prev_rank})")
            report_lines.append("")
            
        # 2. Rank Movers (within Top 50)
        common = curr_tickers.intersection(prev_tickers)
        movers = []
        for t in common:
            rank_curr = list(df_curr['ticker']).index(t) + 1
            rank_prev = list(df_prev['ticker']).index(t) + 1
            diff = rank_prev - rank_curr # Positive means improved rank (e.g. 10 -> 5 = +5)
            if abs(diff) >= 3: # Only noticeable moves
                movers.append((t, diff, rank_curr))
        
        movers.sort(key=lambda x: x[1], reverse=True) # Biggest climbers first
        
        if movers:
            report_lines.append("## 🚀 Significant Rank Movers")
            for t, diff, r in movers:
                icon = "🔼" if diff > 0 else "🔻"
                verdict = get_verdict(t)
                report_lines.append(f"- {icon} **{t}**: {diff:+} positions (Now #{r})")
                report_lines.append(f"  > *AI Verdict*: {verdict}")
            report_lines.append("")

    else:
        report_lines.append("First run. No previous history to compare.")
        
    # Output
    report_text = "\n".join(report_lines)
    print(report_text)
    
    # Save Report
    brief_path = os.path.join(settings.DATA_DIR, 'reports', 'daily_brief.md')
    with open(brief_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    print(f"\nBrief saved to {brief_path}")

if __name__ == "__main__":
    generate_daily_brief()
