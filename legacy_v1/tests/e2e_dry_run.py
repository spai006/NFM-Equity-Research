
import sys
import os
from unittest.mock import patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import run_data_pipeline, run_scoring, run_monitoring

def mock_get_tickers():
    print(">>> [MOCK] Returning small ticker set for Dry Run")
    return ['RELIANCE', 'TCS', 'INFY']

def main():
    print("==========================================")
    print("   DRY RUN: NFM EQUITY RESEARCH PIPELINE   ")
    print("==========================================\n")

    # Patch the ticker source to only run 3 stocks
    with patch('src.pipeline.run_data_pipeline.get_all_nse_tickers', side_effect=mock_get_tickers):
        
        # Step 1: Data Ingestion
        print(">>> STEP 1: DATA INGESTION (Dry Run)")
        try:
            run_data_pipeline.run()
        except Exception as e:
            print(f"!!! FAILURE IN STEP 1: {e}")
            return

        # Step 2: Scoring
        print("\n>>> STEP 2: SCORING (Dry Run)")
        try:
            run_scoring.run()
        except Exception as e:
            print(f"!!! FAILURE IN STEP 2: {e}")
            return

        # Step 3: Monitoring
        print("\n>>> STEP 3: MONITORING (Dry Run)")
        try:
            # We assume monitoring might need previous history, but let's run it to check for crashes
            run_monitoring.generate_daily_brief()
        except Exception as e:
            print(f"!!! FAILURE IN STEP 3: {e}")
            # Step 3 might fail if no history exists, which is expected in a fresh dry run
            pass

    print("\n==========================================")
    print("   DRY RUN COMPLETED")
    print("==========================================")

if __name__ == "__main__":
    main()
