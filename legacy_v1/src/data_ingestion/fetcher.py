
import yfinance as yf
import pandas as pd
from config import settings

def fetch_financials(ticker_symbol):
    """
    Fetches financial data for a given ticker symbol using yfinance.
    
    Args:
        ticker_symbol (str): The stock ticker (e.g., 'RELIANCE'). 
                             Suffix will be added from settings.
    
    Returns:
        dict: Dictionary containing 'financials', 'balance_sheet', 'cashflow' DataFrames.
              Returns None if fetch fails.
    """
    try:
        full_ticker = f"{ticker_symbol}{settings.MARKET_SUFFIX}"
        stock = yf.Ticker(full_ticker)
        
        # Fetching annual data
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cashflow = stock.cashflow
        
        if financials.empty or balance_sheet.empty or cashflow.empty:
            print(f"Warning: Missing data for {full_ticker}")
            return None
            
        return {
            "financials": financials,
            "balance_sheet": balance_sheet,
            "cashflow": cashflow
        }
        
    except Exception as e:
        print(f"Error fetching data for {ticker_symbol}: {e}")
        return None
