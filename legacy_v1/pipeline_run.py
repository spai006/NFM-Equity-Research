
import sys
import os
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.pipeline import run_data_pipeline
from src.pipeline import run_scoring
from src.pipeline import run_monitoring

def main():
    print("==========================================")
    print("   NFM EQUITY RESEARCH AUTOMATION BOT   ")
    print("==========================================\n")
    
    start_total = time.time()
    
    # Step 1: Data Ingestion
    print(">>> STEP 1: DATA INGESTION & PROCESSING")
    try:
        run_data_pipeline.run()
    except Exception as e:
        print(f"!!! CRITICAL FAILURE IN STEP 1: {e}")
        sys.exit(1)
        
    print("\n------------------------------------------\n")
    
    # Step 2: Scoring
    print(">>> STEP 2: SCORING & RANKING")
    try:
        run_scoring.run()
    except Exception as e:
        print(f"!!! CRITICAL FAILURE IN STEP 2: {e}")
        sys.exit(1)
        
    print("\n------------------------------------------\n")

    # Step 3: Monitoring
    print(">>> STEP 3: MONITORING & REPORTING")
    try:
        run_monitoring.generate_daily_brief()
    except Exception as e:
        print(f"!!! CRITICAL FAILURE IN STEP 3: {e}")
        sys.exit(1)
        
    elapsed = time.time() - start_total
    print(f"\n==========================================")
    print(f"   PIPELINE COMPLETED SUCCESSFULLY in {elapsed:.1f}s")
    print("==========================================")

if __name__ == "__main__":
    main()
