
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
        dict: Dictionary containing 'financials', 'balance_sheet', 'cashflow' DataFrames,
              plus 'info' dict and 'history' DataFrame.
              Returns None if fetch fails.
    """
    try:
        full_ticker = f"{ticker_symbol}{settings.MARKET_SUFFIX}"
        stock = yf.Ticker(full_ticker)
        
        # Fetching annual data
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        cashflow = stock.cashflow
        
        # Fetching price history (1 Year) for Price Growth metric
        # period='1y' gives daily data for last year
        history = stock.history(period="1y")
        
        # Fetching info (Market Cap, PEG, etc.)
        # Note: info fetching can be slow or flaky, but it's needed for Market Cap & PEG
        try:
            info = stock.info
        except Exception:
            info = {}
        
        if financials.empty or balance_sheet.empty or cashflow.empty:
            print(f"Warning: Missing data for {full_ticker}")
            return None
            
        return {
            "financials": financials,
            "balance_sheet": balance_sheet,
            "cashflow": cashflow,
            "history": history,
            "info": info
        }
        
    except Exception as e:
        print(f"Error fetching data for {ticker_symbol}: {e}")
        return None
