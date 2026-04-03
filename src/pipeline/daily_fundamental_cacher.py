import sys
from pathlib import Path
import json
import os

# Connect to src modules
proj_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(proj_root))

from src.data_ingestion.universe import Universe
from src.metrics.factors.core_factors import compute_fundamental_factors

def generate_daily_cache():
    print("=" * 50)
    print("🚀 NFM Daily Fundamental Cacher")
    print("=" * 50)
    
    universe = Universe()
    tickers = universe.all_tickers()[:50]
    
    cache_dict = {}
    
    for idx, ticker in enumerate(tickers):
        print(f"[{idx+1}/{len(tickers)}] Fetching deep fundamentals for {ticker}...")
        try:
            factors = compute_fundamental_factors(ticker)
            # Ensure JSON serializable (handling any stray NaNs or numpy types)
            safe_factors = [float(f) if f == f else 0.0 for f in factors]
            cache_dict[ticker] = safe_factors
        except Exception as e:
            print(f"❌ Failed processing {ticker}: {e}")
            cache_dict[ticker] = [0.0] * 10
            
    # Save the cache to the data folder
    data_dir = proj_root / "data"
    data_dir.mkdir(exist_ok=True)
    cache_path = data_dir / "fundamentals_cache.json"
    
    with open(cache_path, "w") as f:
        json.dump(cache_dict, f, indent=4)
        
    print(f"\n✅ Successfully cached {len(cache_dict)} tickers to {cache_path}")

if __name__ == "__main__":
    generate_daily_cache()
