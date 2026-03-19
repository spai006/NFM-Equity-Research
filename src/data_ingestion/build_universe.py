import csv
from pathlib import Path
import pandas as pd

from nselib import capital_market

UNIVERSE_FILE = Path("data/universe_master.csv")

def generate_universe_csv():
    print("Fetching master equity list from NSE...")
    
    # nselib does not have a native nifty500 API. 
    # We fetch the entire NSE master list (~2,000+ stocks) instead
    df = capital_market.equity_list()
    
    # Handle column name variations from NSE
    col_name = 'SYMBOL' if 'SYMBOL' in df.columns else 'Symbol'

    # Slice strictly the first 500 to exactly match the C++ Memory Map size
    tickers = df[col_name].dropna().tolist()[:500]
    
    # Create the data directory if it doesn't exist
    UNIVERSE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(UNIVERSE_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["stock_id", "ticker"])
        
        for stock_id, ticker in enumerate(tickers):
            # Clean up ticker and ensure it's uppercase
            clean_ticker = str(ticker).strip().upper()
            writer.writerow([stock_id, clean_ticker])
            
    print(f"Successfully generated {UNIVERSE_FILE} with {len(tickers)} tickers.")
    print("Your universe.py will now use this exactly as you designed it!")

if __name__ == "__main__":
    generate_universe_csv()
