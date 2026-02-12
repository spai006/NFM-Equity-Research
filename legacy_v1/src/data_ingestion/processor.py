
import pandas as pd
import numpy as np
from config import settings

def get_value_from_mapping(df, mapping_keys, col_idx=0):
    """
    Helper to extract value from DataFrame looking up multiple possible keys.
    Returns np.nan if not found.
    """
    # specific handling for empty dataframe
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
    
    # Ensure columns are sorted by date descending (should be default from yfinance, but safety first)
    # yfinance returns recent first.
    
    # We need:
    # 1. Recent data (latest year) -> index 0
    # 2. 3-year-old data (for CAGR) -> index 3 (if available) -> (0, 1, 2, 3) where 0 is recent.
    
    processed = {"ticker": ticker}
    
    # Mapping
    mapping = settings.YAHOO_MAPPING
    
    # --- Profitability ---
    processed["net_income"] = get_value_from_mapping(financials, mapping["net_income"], 0)
    processed["equity"] = get_value_from_mapping(balance_sheet, mapping["equity"], 0)
    
    ebit = get_value_from_mapping(financials, mapping["ebit"], 0)
    processed["ebit"] = ebit
    
    # Capital Employed = Total Assets - Current Liabilities
    # Or just Equity + Non-Current Liabilities.
    # Let's try Total Assets - Current Liab
    tot_assets = get_value_from_mapping(balance_sheet, mapping["total_assets"], 0)
    curr_liab = get_value_from_mapping(balance_sheet, mapping["current_liabilities"], 0)
    
    if not pd.isna(tot_assets) and not pd.isna(curr_liab):
        processed["capital_employed"] = tot_assets - curr_liab
    else:
        # Fallback: Equity + Total Debt (rough proxy if liabilities missing)
        tot_debt = get_value_from_mapping(balance_sheet, mapping["total_debt"], 0)
        equity = processed["equity"]
        if not pd.isna(tot_debt) and not pd.isna(equity):
             processed["capital_employed"] = equity + tot_debt
        else:
             processed["capital_employed"] = np.nan

    processed["revenue"] = get_value_from_mapping(financials, mapping["revenue"], 0)
    
    # --- Growth ---
    processed["revenue_3y_ago"] = get_value_from_mapping(financials, mapping["revenue"], 3)
    processed["profit_3y_ago"] = get_value_from_mapping(financials, mapping["net_income"], 3)
    
    # --- Leverage ---
    processed["total_debt"] = get_value_from_mapping(balance_sheet, mapping["total_debt"], 0)
    processed["interest_expense"] = get_value_from_mapping(financials, mapping["interest_expense"], 0)
    # Interest expense is often negative in data, take absolute
    if not pd.isna(processed["interest_expense"]):
        processed["interest_expense"] = abs(processed["interest_expense"])
        
    # --- Cash Flow ---
    processed["cfo"] = get_value_from_mapping(cashflow, mapping["cfo"], 0)
    processed["capex"] = get_value_from_mapping(cashflow, mapping["capex"], 0)
    # Capex is usually negative, make it positive for calculation if metric formula expects substraction (cfo - capex)
    # wait, compute_metrics.py says: return cfo - capex.
    # If capex is negative (-100), cfo is positive (200), FCF = 200 - (-100) = 300? No.
    # FCF = Operating Cash Flow - Capital Expenditures.
    # Usually FCF = OCF - |Capex|.
    # Let's check compute_metrics logic: `return cfo - capex`.
    # If data comes as negative, it becomes addition.
    # Yahoo usually reports Capex as negative.
    # So `cfo - (-100)` = `cfo + 100`. This increases FCF which is WRONG.
    # FCF should be less than CFO.
    # So if Capex is negative, we should ADD it (200 + (-100) = 100).
    # OR change compute_metrics? No, I shouldn't change compute metrics if I can avoid it.
    # Let's look at compute_metrics `free_cash_flow`: `return cfo - capex`.
    # If I pass positive Capex, it works: 200 - 100 = 100.
    # So I must ensure 'capex' in processed data is POSITIVE.
    if not pd.isna(processed["capex"]) and processed["capex"] < 0:
        processed["capex"] = abs(processed["capex"])
        
    # --- Efficiency ---
    processed["total_assets"] = tot_assets
    
    # --- Missing Fields needed by compute_all_metrics ---
    # compute_all_metrics takes 'row' and accesses keys.
    # We must ensure all keys exist even if NaN.
    for field in settings.REQUIRED_FIELDS:
        if field not in processed:
            processed[field] = np.nan
            
    return processed
