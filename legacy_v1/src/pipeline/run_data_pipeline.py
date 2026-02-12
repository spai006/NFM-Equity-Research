
import pandas as pd
import os
import sys
from tqdm import tqdm
import nselib
from nselib import capital_market

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import settings
from src.data_ingestion import fetcher, processor
from src.metrics import compute_metrics

def get_all_nse_tickers():
    """
    Fetches the list of all equity tickers from NSE using nselib.
    Returns a list of ticker symbols.
    """
    try:
        print("Fetching equity list from NSE...")
        # equity_list returns a DataFrame with 'SYMBOL' column
        df = capital_market.equity_list()
        tickers = df['SYMBOL'].tolist()
        # Filter out ETFs or weird symbols if needed, but usually SYMBOL is clean
        return tickers
    except Exception as e:
        print(f"Error fetching NSE ticker list: {e}")
        return []

def run():
    print("Starting Data Pipeline for Full Universe...")
    
    # 1. Get Tickers
    all_tickers = get_all_nse_tickers()
    if not all_tickers:
        print("No tickers found. Exiting.")
        return
        
    print(f"Total tickers found: {len(all_tickers)}")
    
    # 2. Resumability Logic
    output_path = settings.PROCESSED_DATA_PATH
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    processed_tickers = set()
    if os.path.exists(output_path):
        try:
            existing_df = pd.read_csv(output_path)
            processed_tickers = set(existing_df['ticker'].tolist())
            print(f"Resuming... {len(processed_tickers)} tickers already processed.")
        except Exception:
            print("Could not read existing file. Starting from scratch.")
            
    # Remove processed from todo
    tickers_to_process = [t for t in all_tickers if t not in processed_tickers]
    print(f"Tickers remaining to process: {len(tickers_to_process)}")
    
    if not tickers_to_process:
        print("All tickers processed!")
        return

    # 3. Processing Loop (Parallelized)
    batch_data = []
    BATCH_SIZE = 10 
    MAX_WORKERS = 5 # Moderate concurrency to respect API limits
    
    import concurrent.futures
    
    print(f"Starting parallel processing with {MAX_WORKERS} workers...")
    
    def process_one_ticker(ticker):
        """Helper to run the full chain for one ticker"""
        # A. Fetch
        raw_data = fetcher.fetch_financials(ticker)
        if not raw_data:
            return None
            
        # B. Process
        processed_data = processor.process_ticker_data(ticker, raw_data)
        if not processed_data:
            return None
            
        # C. Compute Metrics
        try:
            metrics = compute_metrics.compute_all_metrics(processed_data)
        except Exception:
            metrics = {}
            
        return {**processed_data, **metrics}

    # Use tqdm for progress bar
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_ticker = {executor.submit(process_one_ticker, t): t for t in tickers_to_process}
        
        # Process as they complete
        progress_bar = tqdm(concurrent.futures.as_completed(future_to_ticker), total=len(tickers_to_process), desc="Processing Stocks", unit="ticker")
        
        for future in progress_bar:
            ticker = future_to_ticker[future]
            try:
                result = future.result()
                if result:
                    batch_data.append(result)
            except Exception as e:
                # Log error but don't stop
                pass
            
            # D. Batch Save (Thread-safe because we are in the main thread consuming results)
            if len(batch_data) >= BATCH_SIZE:
                save_batch(batch_data, output_path)
                batch_data = [] # Clear buffer

    # Save remaining
    if batch_data:
        save_batch(batch_data, output_path)
        
    print("Pipeline completed.")

def save_batch(new_data, path):
    """
    Appends a batch of data to the CSV file.
    Reads existing headers if file exists to ensure column order.
    """
    if not new_data:
        return
        
    df_batch = pd.DataFrame(new_data)
    
    # Standardize columns order based on existing file or settings
    # If file exists, align columns
    if os.path.exists(path):
        # We append mode='a', no header
        # Need to ensure columns match the existing file's order
        existing_header = pd.read_csv(path, nrows=0).columns.tolist()
        
        # Add missing cols to batch with NaN
        for col in existing_header:
            if col not in df_batch.columns:
                df_batch[col] = pd.NA
                
        # Reorder batch to match existing
        df_batch = df_batch[existing_header]
        
        df_batch.to_csv(path, mode='a', header=False, index=False)
    else:
        # New file
        # Put ticker first
        cols = ['ticker'] + [c for c in df_batch.columns if c != 'ticker']
        df_batch = df_batch[cols]
        df_batch.to_csv(path, mode='w', header=True, index=False)

if __name__ == "__main__":
    run()
