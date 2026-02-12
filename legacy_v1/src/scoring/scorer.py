
import pandas as pd
import numpy as np
from config import settings

def normalize_metrics(df):
    """
    Normalizes metrics using Percentile Ranking (0 to 1).
    Handles directionality (Lower is Better vs Higher is Better).
    """
    # Create a copy to avoid SettingWithCopy warnings
    scored_df = df.copy()
    
    # List of metrics where Lower is Better
    # We will invert the rank for these: 1 - percentile
    LOWER_IS_BETTER = settings.LOWER_IS_BETTER 
    
    weights = settings.SCORING_WEIGHTS
    
    # Compute weighted score
    # score = sum( percentile(metric) * weight )
    
    # Initialize total score
    scored_df['final_score'] = 0.0
    
    for metric, weight in weights.items():
        if metric not in scored_df.columns:
            continue
            
        # Ensure column is numeric (handle 'N/A', strings, etc.)
        scored_df[metric] = pd.to_numeric(scored_df[metric], errors='coerce')
        
        # 1. Compute Percentile (rank / count)
        # Handle NaNs: they get rank NaN, so fill with median or 0?  
        # Better to fill with a low rank (0) so they don't appear in top lists.
        # But for 'debt', missing might mean 0 debt (good)? No, assume 0 for missing debt.
        # Let's rely on processor.py dealing with NaNs or filling defaults.
        # If NaN, let's just skip contributing to score (treat as neutral or bad).
        # We'll fillna with median for ranking robustness, or 
        # actually, pandas rank handles NaN by assigning them NaN or keeping them out.
        # Let's fill NaNs with worst possible value for the metric before ranking to penalize missing data.
        
        series = scored_df[metric]
        
        if metric in LOWER_IS_BETTER:
            # For lower is better (e.g. Debt), fill NaNs with a High Value (Max)
            series_filled = series.fillna(series.max())
            # Rank Ascending (Low values = Low Rank Number). 
            # We want Low Debt = High Score.
            # pct=True gives 0 to 1. 0 = lowest debt, 1 = highest debt.
            # So we invert: 1 - rank.
            percentile = series_filled.rank(pct=True, ascending=True)
            score_contribution = (1 - percentile) * weight
        else:
            # For higher is better (e.g. ROE), fill NaNs with Low Value (Min)
            series_filled = series.fillna(series.min())
            percentile = series_filled.rank(pct=True, ascending=True)
            score_contribution = percentile * weight
            
        # Add to total
        scored_df['final_score'] += score_contribution
        
        # Store individual component score for debugging/explainability
        scored_df[f'score_{metric}'] = score_contribution

    return scored_df

def get_top_n(df, n=50):
    """
    Returns the top N companies based on 'final_score'.
    """
    if 'final_score' not in df.columns:
        return pd.DataFrame() # Empty
        
    return df.sort_values(by='final_score', ascending=False).head(n)
