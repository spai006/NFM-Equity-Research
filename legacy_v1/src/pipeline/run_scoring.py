
import pandas as pd
import os
import sys

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import settings
from src.scoring import scorer
from src.llm_reasoning import prompts

def run():
    print("Starting Scoring Pipeline...")
    
    # 1. Load Data
    input_path = settings.PROCESSED_DATA_PATH
    if not os.path.exists(input_path):
        print(f"Error: Processed data not found at {input_path}")
        return
        
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} companies.")
    
    if df.empty:
        return

    # 2. Score
    scored_df = scorer.normalize_metrics(df)
    
    # 3. Rank
    top_50 = scorer.get_top_n(scored_df, n=50)
    
    if top_50.empty:
        print("No companies passed scoring.")
        return
        
    print("Top 5 Scored Companies:")
    print(top_50[['ticker', 'final_score', 'roe', 'revenue_cagr']].head())
    
    # 4. Generate Prompts (Sample for top 5)
    print("\nGenerating Prompts for Top 5...")
    top_50['llm_prompt'] = ""
    
    for idx, row in top_50.iterrows():
        # Rank is simply row number in listing (1-based)
        rank = list(top_50.index).index(idx) + 1
        prompt = prompts.generate_justification_prompt(row, rank)
        top_50.at[idx, 'llm_prompt'] = prompt
        
        if rank <= 1:
            print("\n--- SAMPLE PROMPT (Rank 1) ---")
            print(prompt)
            print("------------------------------\n")

    # 5. Save Output
    # 5. Save Output
    from datetime import datetime
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    # Save Latest
    output_path = os.path.join(settings.DATA_DIR, 'reports', 'top_50.csv')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    top_50.to_csv(output_path, index=False)
    
    # Save History
    history_path = os.path.join(settings.DATA_DIR, 'reports', 'history', f'top_50_{today_str}.csv')
    os.makedirs(os.path.dirname(history_path), exist_ok=True)
    top_50.to_csv(history_path, index=False)
    
    print(f"Top 50 list saved to {output_path}")
    print(f"History snapshot saved to {history_path}")

if __name__ == "__main__":
    run()
