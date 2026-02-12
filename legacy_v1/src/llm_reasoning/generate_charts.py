import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# Setup
plt.style.use('bmh') # Clean aesthetic
logging_handler = sys.stdout

def generate_charts(input_file, assets_dir):
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"File not found: {input_file}")
        return

    # Ensure assets dir exists
    os.makedirs(assets_dir, exist_ok=True)
    
    # 1. Top 50 Scores Bar Chart
    top_50 = df.head(50).copy()
    top_50 = top_50.sort_values(by='final_score', ascending=True) # Sort for barh

    # Increase height to accommodate 50 bars
    plt.figure(figsize=(12, 14))
    bars = plt.barh(top_50['ticker'], top_50['final_score'], color='#2c3e50')
    
    plt.title('Top 50 Companies by Fundamental Score', fontsize=16, pad=20)
    plt.xlabel('Composite Score')
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    
    # Check if final_score exists
    if 'final_score' not in top_50.columns:
        print("Error: 'final_score' column missing.")
        return
    
    # Add values to bars
    for bar in bars:
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2, 
                 f'{width:.2f}', 
                 ha='left', va='center', fontsize=9)

    output_path = os.path.join(assets_dir, 'top50_scores.png')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Generated {output_path}")

if __name__ == "__main__":
    from config import settings
    INPUT = os.path.join(settings.DATA_DIR, 'reports', 'top_50.csv')
    OUTPUT_DIR = os.path.join(settings.DATA_DIR, 'reports', 'assets')
    
    generate_charts(INPUT, OUTPUT_DIR)
