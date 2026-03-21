import mmap
import ctypes
import numpy as np
import pandas as pd
from pathlib import Path
import sys

import time

start = time.perf_counter()

# Connect to our src modules
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.data_ingestion.universe import Universe
from src.metrics.factors.momentum import compute_fundamental_factors

class Record(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("stock_id", ctypes.c_int32),
        ("factors", ctypes.c_double * 10)
    ]

class SharedBlock(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("count", ctypes.c_uint32),
        ("records", Record * 50)
    ]

def normalize_zscore(series: pd.Series):
    """
    Standard Z-score normalization: (x - mean) / std.
    Replaces NaNs with 0 (market average) to prevent C++ from choking on null data.
    """
    mean = series.mean()
    std = series.std()
    
    if std == 0 or pd.isna(std):
        # If variance is zero, all values are the mean, so Z-Score is universally 0
        return pd.Series(0.0, index=series.index)
        
    normalized = (series - mean) / std
    
    # Fill any remaining NaNs (eg from missing IPO data) with 0.0 (neutral cross-sectional score)
    return normalized.fillna(0.0)

def main():
    print("--- Starting Fundamental Factor Engine ---")
    universe = Universe()
    tickers = universe.all_tickers()
    
    # We strictly enforce the 50 limit for our C++ struct arrays
    tickers = tickers[:50]
    
    print(f"Loaded {len(tickers)} tickers from Universe mappings.")
    
    # 1. Loop and assemble raw matrix
    raw_factors_matrix = []
    
    for idx, ticker in enumerate(tickers):
        print(f"[{idx+1}/{len(tickers)}] Computing fundamentals for {ticker}...")
        
        # Returns [pe, peg, rev_growth_1y, rev_cagr, eps_growth, roe, roce, fcf_np, fcf_rev, debt_equity]
        factors = compute_fundamental_factors(ticker)
        
        raw_factors_matrix.append({
            "stock_id": universe.get_id(ticker),
            "f0_pe": factors[0],
            "f1_peg": factors[1],
            "f2_rev_growth_1y": factors[2],
            "f3_rev_cagr_10y": factors[3],
            "f4_eps_growth": factors[4],
            "f5_roe": factors[5],
            "f6_roce": factors[6],
            "f7_fcf_np": factors[7],
            "f8_fcf_rev": factors[8],
            "f9_debt_equity": factors[9]
        })
        
    df_raw = pd.DataFrame(raw_factors_matrix)
    
    # 2. Normalize column-wise across the entire 50 stock cross-section
    print("\nNavigating cross-sectional normalization (Z-Scoring)...")
    df_norm = pd.DataFrame()
    df_norm['stock_id'] = df_raw['stock_id']
    
    # Apply standard normalization for all 10 factors
    factor_cols = [
        'f0_pe', 'f1_peg', 'f2_rev_growth_1y', 'f3_rev_cagr_10y', 
        'f4_eps_growth', 'f5_roe', 'f6_roce', 'f7_fcf_np', 
        'f8_fcf_rev', 'f9_debt_equity'
    ]
    
    for col in factor_cols:
        df_norm[col] = normalize_zscore(df_raw[col])
    
    # 3. Write directly to Shared Memory
    print("Writing normalized Factor Matrix to Memory-Mapped IPC Block...")
    
    # FIX: Use local path for Windows compatibility instead of /tmp/
    filename = "market_state.bin"
    file_size = ctypes.sizeof(SharedBlock)
    
    # Pre-allocate exactly 4204 bytes
    with open(filename, "wb") as f:
        f.truncate(file_size)
        
    with open(filename, "r+b") as f:
        mm = mmap.mmap(f.fileno(), file_size, access=mmap.ACCESS_WRITE)
        block = SharedBlock.from_buffer(mm)
        
        block.count = len(df_norm)
        
        for i, row in df_norm.iterrows():
            block.records[i].stock_id = int(row['stock_id'])
            
            # Dump pre-normalized float data directly into C++ RAM space
            block.records[i].factors[0] = row['f0_pe']
            block.records[i].factors[1] = row['f1_peg']
            block.records[i].factors[2] = row['f2_rev_growth_1y']
            block.records[i].factors[3] = row['f3_rev_cagr_10y']
            block.records[i].factors[4] = row['f4_eps_growth']
            block.records[i].factors[5] = row['f5_roe']
            block.records[i].factors[6] = row['f6_roce']
            block.records[i].factors[7] = row['f7_fcf_np']
            block.records[i].factors[8] = row['f8_fcf_rev']
            block.records[i].factors[9] = row['f9_debt_equity']
                
        del block
        mm.close()
        
    print("\n✅ SUCCESS: 50 Normalized Rows written directly to IPC Shared Memory.")
    print("🚀 Next Step: Run main.cpp to let the C++ Execution Core generate the ranking!")

if __name__ == "__main__":
    main()
    
    end = time.perf_counter()
    print(f"\nFactor Engine Runtime: {(end-start):.3f} sec")
    print(f"Stocks/sec: {50 / (end-start):.2f}")