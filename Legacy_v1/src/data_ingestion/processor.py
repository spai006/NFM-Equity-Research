
import pandas as pd
import numpy as np
from config import settings

def get_value_from_mapping(df, mapping_keys, col_idx=0):
    """
    Helper to extract value from DataFrame looking up multiple possible keys.
    Returns np.nan if not found.
    """
    if df.empty:
        return np.nan
        
    try:
        col_name = df.columns[col_idx]
    except IndexError:
        return np.nan
        
    for key in mapping_keys:
        if key in df.index:
            try:
                val = df.loc[key, col_name]
                return float(val) if val is not None else np.nan
            except Exception:
                continue
                
    return np.nan

def get_series_from_mapping(df, mapping_keys):
    """
    Helper to extract a row as a series (history) from DataFrame looking up keys.
    Returns None if not found.
    """
    if df.empty:
        return None
        
    for key in mapping_keys:
        if key in df.index:
            try:
                # Return the row as numeric series, dropping NaNs if needed, but keeping index order
                # yfinance cols are dates.
                return pd.to_numeric(df.loc[key], errors='coerce')
            except Exception:
                continue
    return None

def process_ticker_data(ticker, raw_data):
    """
    Extracts required fields from raw Yahoo Finance data.
    Returns a dictionary suitable for metric computation.
    """
    if not raw_data:
        return None
        
    financials = raw_data.get('financials', pd.DataFrame())
    balance_sheet = raw_data.get('balance_sheet', pd.DataFrame())
    cashflow = raw_data.get('cashflow', pd.DataFrame())
    history = raw_data.get('history', pd.DataFrame())
    info = raw_data.get('info', {})
    
    mapping = settings.YAHOO_MAPPING
    processed = {"ticker": ticker}
    
    # --- HELPER: Extract Histories for "10Y" Metrics ---
    # We will store lists/series of values to compute averages/CAGRs later in compute_metrics
    # Or pre-compute them here? Better to extract raw series here and compute in metrics.
    # But compute_metrics `compute_all_metrics` expects a flat 'row'.
    # So we should compute complex aggregations here or Flatten them.
    # I will extract Series here but for the flat 'row' passing, I will pre-calculate the "10y" aggregates here
    # OR change compute_metrics logic.
    # To keep compute_metrics pure, I will extract "Series" into special keys like "hist_revenue" 
    # and then compute_metrics can use them. 
    # Wait, `compute_metrics.compute_all_metrics(row)` takes a flat dict.
    # So I will calculate the "10Y" aggregates here? No, that puts logic in processor.
    # I will put logic in compute_metrics, but I need to pass the data.
    # I will add fields like "hist_revenue", "hist_net_income" to the processed dict.
    
    revenue_series = get_series_from_mapping(financials, mapping["revenue"])
    net_income_series = get_series_from_mapping(financials, mapping["net_income"])
    ebit_series = get_series_from_mapping(financials, mapping["ebit"])
    equity_series = get_series_from_mapping(balance_sheet, mapping["equity"])
    eps_series = get_series_from_mapping(financials, mapping["eps"])
    gross_profit_series = get_series_from_mapping(financials, mapping["gross_profit"])
    total_assets_series = get_series_from_mapping(balance_sheet, mapping["total_assets"])
    curr_liab_series = get_series_from_mapping(balance_sheet, mapping["current_liabilities"])
    
    # Capital Employed Series
    cap_employed_series = None
    if total_assets_series is not None and curr_liab_series is not None:
        cap_employed_series = total_assets_series - curr_liab_series
        
    # Store these series in processed (as list or delimited string? No, just list if we stay in python)
    # But if we save to CSV, lists are bad.
    # Ideally, compute_metrics runs IN MEMORY before saving to CSV.
    # The pipeline step "C. Compute Metrics" runs right after processing.
    # So passing lists in dict is fine.
    
    processed["hist_revenue"] = revenue_series.tolist() if revenue_series is not None else []
    processed["hist_net_income"] = net_income_series.tolist() if net_income_series is not None else []
    processed["hist_ebit"] = ebit_series.tolist() if ebit_series is not None else []
    processed["hist_equity"] = equity_series.tolist() if equity_series is not None else []
    processed["hist_cap_employed"] = cap_employed_series.tolist() if cap_employed_series is not None else []
    processed["hist_eps"] = eps_series.tolist() if eps_series is not None else []
    processed["hist_gross_profit"] = gross_profit_series.tolist() if gross_profit_series is not None else []
    
    # --- Single Point Values (Latest) ---
    processed["net_income"] = get_value_from_mapping(financials, mapping["net_income"], 0)
    processed["equity"] = get_value_from_mapping(balance_sheet, mapping["equity"], 0)
    processed["ebit"] = get_value_from_mapping(financials, mapping["ebit"], 0)
    processed["revenue"] = get_value_from_mapping(financials, mapping["revenue"], 0)
    processed["gross_profit"] = get_value_from_mapping(financials, mapping["gross_profit"], 0) # New
    processed["eps"] = get_value_from_mapping(financials, mapping["eps"], 0) # New
    
    # Capital Employed Latest
    tot_assets = get_value_from_mapping(balance_sheet, mapping["total_assets"], 0)
    curr_liab = get_value_from_mapping(balance_sheet, mapping["current_liabilities"], 0)
    if not pd.isna(tot_assets) and not pd.isna(curr_liab):
        processed["capital_employed"] = tot_assets - curr_liab
    else:
        # Fallback
        tot_debt = get_value_from_mapping(balance_sheet, mapping["total_debt"], 0)
        if not pd.isna(tot_debt) and not pd.isna(processed["equity"]):
             processed["capital_employed"] = processed["equity"] + tot_debt
        else:
             processed["capital_employed"] = np.nan

    processed["total_assets"] = tot_assets
    
    # --- Leverage ---
    processed["total_debt"] = get_value_from_mapping(balance_sheet, mapping["total_debt"], 0)
    processed["interest_expense"] = get_value_from_mapping(financials, mapping["interest_expense"], 0)
    if not pd.isna(processed["interest_expense"]):
        processed["interest_expense"] = abs(processed["interest_expense"])
        
    processed["total_liabilities"] = get_value_from_mapping(balance_sheet, mapping["total_liabilities"], 0) # New
        
    # --- Cash Flow ---
    processed["cfo"] = get_value_from_mapping(cashflow, mapping["cfo"], 0)
    processed["cfi"] = get_value_from_mapping(cashflow, mapping["cfi"], 0) # New
    processed["capex"] = get_value_from_mapping(cashflow, mapping["capex"], 0)
    if not pd.isna(processed["capex"]) and processed["capex"] < 0:
        processed["capex"] = abs(processed["capex"])
        
    # --- Receivables ---
    processed["receivables"] = get_value_from_mapping(balance_sheet, mapping["receivables"], 0)

    # --- Market / Info Data ---
    # PEG
    processed["peg_ratio"] = info.get('pegRatio', np.nan)
    # Market Cap
    processed["market_cap"] = info.get('marketCap', np.nan)
    if pd.isna(processed["market_cap"]):
        # Try fast info not available here, but info usually has it.
        # Fallback: Price * Shares?
        pass
        
    # Price
    # Get latest close from history
    if not history.empty:
        processed["price_current"] = history['Close'].iloc[-1]
        try:
             # 1 year ago (approx 252 trading days)
             # or just take the first record if we fetched 1y
             processed["price_1y_ago"] = history['Close'].iloc[0]
        except Exception:
             processed["price_1y_ago"] = np.nan
    else:
        processed["price_current"] = info.get('currentPrice', np.nan)
        processed["price_1y_ago"] = np.nan

    # --- Growth Legacy (3Y) --- (Keeping for backward compat or other metrics)
    processed["revenue_3y_ago"] = get_value_from_mapping(financials, mapping["revenue"], 3)
    processed["profit_3y_ago"] = get_value_from_mapping(financials, mapping["net_income"], 3)

    return processed
