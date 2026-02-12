import json
import logging
import os
import sys

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def compile_report(explanations_file, output_file):
    logging.info(f"Loading explanations from {explanations_file}")
    try:
        with open(explanations_file, 'r') as f:
            explanations = json.load(f)
    except FileNotFoundError:
        logging.error(f"Explanations file not found: {explanations_file}")
        sys.exit(1)

    logging.info(f"Compiling report for {len(explanations)} companies...")
    
    with open(output_file, 'w') as f:
        # Title
        f.write("# Top 50 Fundamental Equity Analysis Report\n\n")
        
        # Methodology Note
        f.write("## Methodology Note\n")
        f.write("This report presents LLM-generated fundamental explanations for the Top 50 ranked Indian companies. ")
        f.write("Rankings are based on a weighted composite score derived from profitability, growth, balance sheet strength, ")
        f.write("valuation, and stability metrics. The explanations aim to provide human-readable justification for model decisions.\n\n")
        
        # Chart
        f.write("## Score Distribution Snapshot\n")
        f.write("![Top 50 Composite Scores](assets/top50_scores.png)\n\n")
        
        # Compile each company
        for idx, item in enumerate(explanations):
            rank = idx + 1
            ticker = item['ticker']
            text = item['explanation']
            
            f.write(f"## Rank {rank} – {ticker}\n\n")
            f.write(text)
            f.write("\n\n")
            
    logging.info(f"Report compiled successfully at {output_file}")

if __name__ == "__main__":
    from config import settings
    INPUT = os.path.join(settings.DATA_DIR, 'reports', 'llm_explanations.json')
    OUTPUT = os.path.join(settings.DATA_DIR, 'reports', 'top_50_analysis.md')
    
    compile_report(INPUT, OUTPUT)
