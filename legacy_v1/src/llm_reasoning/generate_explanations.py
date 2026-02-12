import pandas as pd
import sys
import os
import json
import logging
import time
import google.generativeai as genai

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Adjust path to import modules if necessary
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(base_dir)

from src.llm_reasoning import prompts

def generate_explanations(input_file, prompt_file, output_file):
    logging.info(f"Loading data from {input_file}")
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        logging.error(f"Input file not found: {input_file}")
        sys.exit(1)
        
    logging.info(f"Loading prompt template from {prompt_file}")
    try:
        with open(prompt_file, 'r') as f:
            template = f.read()
    except FileNotFoundError:
        logging.error(f"Prompt output file not found: {prompt_file}")
        sys.exit(1)

    # Since we lack 'sector' and 'alerts' in top_50.csv currently, 
    # we will provide placeholders or derive/fill them to avoid breaking the script.
    # PROMPT asked for "Active Alerts (if any)". If missing, we say "None".
    # PROMPT asked for "Sector". If missing, we say "N/A".
    
    if 'sector' not in df.columns:
        df['sector'] = 'N/A'
    if 'alerts' not in df.columns:
        df['alerts'] = 'None'

    results = []

    logging.info(f"Generating explanations for {len(df)} companies...")

    # Configure Gemini
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY not found in environment variables.")
        sys.exit(1)
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-latest')
    
    
    for idx, row in df.iterrows():
        # Format the prompt
        try:
            # Handle potential NaN values safely for formatting
            def safe_float(val):
                return float(val) if pd.notnull(val) else 0.0
            
            prompt = template.format(
                ticker=row.get('ticker', 'Unknown'),
                sector=row.get('sector', 'N/A'),
                final_score=f"{safe_float(row.get('final_score')):.2f}",
                roe=safe_float(row.get('roe')),
                roce=safe_float(row.get('roce')),
                net_margin=safe_float(row.get('net_margin')),
                revenue_cagr=safe_float(row.get('revenue_cagr')),
                profit_cagr=safe_float(row.get('profit_cagr')),
                debt_to_equity=safe_float(row.get('debt_to_equity')),
                interest_coverage=safe_float(row.get('interest_coverage')),
                asset_turnover=safe_float(row.get('asset_turnover')),
                alerts=row.get('alerts', 'None')
            )
            
            # Call Gemini API
            try:
                response = model.generate_content(prompt)
                llm_response = response.text
                logging.info(f"Generated explanation for {row.get('ticker')}")
                # Rate limit handling (Free tier is approx 15 RPM = 1 request every 4s)
                time.sleep(4) 
            except Exception as api_err:
                logging.error(f"Gemini API Error for {row.get('ticker')}: {api_err}")
                llm_response = "Error generating explanation due to API failure."
                time.sleep(10) # Backoff on error
            results.append({
                'ticker': row['ticker'],
                'explanation': llm_response.strip()
            })
            
        except Exception as e:
            logging.error(f"Error processing {row.get('ticker')}: {e}")
            
    # Save results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
        
    logging.info(f"Saved {len(results)} explanations to {output_file}")


if __name__ == "__main__":
    # Define paths relative to repo root
    from config import settings
    BASE = settings.BASE_DIR
    INPUT = os.path.join(settings.DATA_DIR, 'reports', 'top_50.csv')
    TEMPLATE = os.path.join(BASE, 'src', 'llm_reasoning', 'prompt_template.txt')
    OUTPUT = os.path.join(settings.DATA_DIR, 'reports', 'llm_explanations.json')
    
    generate_explanations(INPUT, TEMPLATE, OUTPUT)
