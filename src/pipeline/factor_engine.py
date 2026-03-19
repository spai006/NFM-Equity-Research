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
from src.metrics.factors.momentum import compute_momentum_factors

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
        ("records", Record * 500)
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
    print("--- Starting Factor Engine ---")
    universe = Universe()
    tickers = universe.all_tickers()
    
    # We strictly enforce the 500 limit for our C++ struct arrays
    tickers = tickers[:500]
    
    print(f"Loaded {len(tickers)} tickers from Universe mappings.")
    
    # 1. Loop and assemble raw matrix
    raw_factors_matrix = []
    
    for idx, ticker in enumerate(tickers):
        print(f"[{idx+1}/{len(tickers)}] Computing momentum for {ticker}...")
        
        # compute_momentum_factors returns [mom_6m, mom_12m, vol, price_to_dma]
        factors = compute_momentum_factors(ticker)
        
        raw_factors_matrix.append({
            "stock_id": universe.get_id(ticker),
            "f0_mom6m": factors[0],
            "f1_mom12m": factors[1],
            "f2_vol": factors[2],
            "f3_p2dma": factors[3]
        })
        
    df_raw = pd.DataFrame(raw_factors_matrix)
    
    # 2. Normalize column-wise across the entire 500 stock cross-section
    print("\nNavigating cross-sectional normalization (Z-Scoring)...")
    df_norm = pd.DataFrame()
    df_norm['stock_id'] = df_raw['stock_id']
    
    # Apply standard normalization
    df_norm['f0_mom6m'] = normalize_zscore(df_raw['f0_mom6m'])
    df_norm['f1_mom12m'] = normalize_zscore(df_raw['f1_mom12m'])
    df_norm['f2_vol'] = normalize_zscore(df_raw['f2_vol'])
    df_norm['f3_p2dma'] = normalize_zscore(df_raw['f3_p2dma'])
    
    # 3. Write directly to Shared Memory
    print("Writing normalized Factor Matrix to Memory-Mapped IPC Block...")
    filename = "/tmp/market_state.bin"
    file_size = ctypes.sizeof(SharedBlock)
    
    # Pre-allocate exactly 42004 bytes
    with open(filename, "wb") as f:
        f.truncate(file_size)
        
    with open(filename, "r+b") as f:
        mm = mmap.mmap(f.fileno(), file_size, access=mmap.ACCESS_WRITE)
        block = SharedBlock.from_buffer(mm)
        
        block.count = len(df_norm)
        
        for i, row in df_norm.iterrows():
            block.records[i].stock_id = int(row['stock_id'])
            
            # Dump pre-normalized float data directly into C++ RAM space
            block.records[i].factors[0] = row['f0_mom6m']
            block.records[i].factors[1] = row['f1_mom12m']
            block.records[i].factors[2] = row['f2_vol']
            block.records[i].factors[3] = row['f3_p2dma']
            
            # Zero-out the remaining 6 unused factors for safe computation
            for j in range(4, 10):
                block.records[i].factors[j] = 0.0
                
        del block
        mm.close()
        
    print("\n✅ SUCCESS: 500 Normalized Rows written directly to IPC Shared Memory.")
    print("🚀 Next Step: Run main.cpp to let the C++ Execution Core generate the ranking!")

if __name__ == "__main__":
    main()
    
    end = time.perf_counter()
    print(f"\nFactor Engine Runtime: {(end-start):.3f} sec")
    print(f"Stocks/sec: {500 / (end-start):.2f}")