# make a fucntion where it should recieve a ticker, append a .NS to it, and then use the python
# yfinance library to fetch the data and compute the momentum factors
# 4 math parameters: 
# 1. 6 month momentum
# 2. 12 month momentum
# 3. rolling volatility
# 4. price to 200-DMA


import yfinance as yf
import numpy as np
import pandas as pd


TRADING_DAYS_6M = 126
TRADING_DAYS_12M = 252
VOL_WINDOW = 63
DMA_200 = 200

def compute_momentum_factors(ticker_symbol: str): 
    ticker = ticker_symbol.strip().upper() + ".NS"

    df = yf.download(
        ticker,
        period="2y",
        auto_adjust=True,
        progress=False
    )

    if df.empty or len(df) < TRADING_DAYS_12M + 5:
        # insufficient history → return NaNs
        return [np.nan, np.nan, np.nan, np.nan]

    close = df["Close"].dropna()

    # Extract scalars proactively to prevent Pandas "FutureWarning" on Series float casting
    current_price = float(close.iloc[-1].item() if isinstance(close.iloc[-1], pd.Series) else close.iloc[-1])
    price_6m = float(close.iloc[-TRADING_DAYS_6M].item() if isinstance(close.iloc[-TRADING_DAYS_6M], pd.Series) else close.iloc[-TRADING_DAYS_6M])
    price_12m = float(close.iloc[-TRADING_DAYS_12M].item() if isinstance(close.iloc[-TRADING_DAYS_12M], pd.Series) else close.iloc[-TRADING_DAYS_12M])

    # --- 6M momentum ---
    mom_6m = (current_price / price_6m) - 1.0

    # --- 12M momentum ---
    mom_12m = (current_price / price_12m) - 1.0

    # --- rolling volatility (3M std of returns) ---
    returns = close.pct_change()
    vol_val = returns.tail(VOL_WINDOW).std()
    vol = float(vol_val.item() if isinstance(vol_val, pd.Series) else vol_val) * np.sqrt(252)

    # --- price vs 200DMA ---
    dma_val = close.rolling(DMA_200).mean().iloc[-1]
    dma_200_flt = float(dma_val.item() if isinstance(dma_val, pd.Series) else dma_val)
    price_to_dma = (current_price / dma_200_flt) - 1.0

    return [
        mom_6m,
        mom_12m,
        vol,
        price_to_dma,
    ]
    
def compute_fundamental_factors(ticker_symbol: str):
    """
    Computes 10 fundamental metrics using yfinance:
    1. P/E
    2. PEG
    3. Revenue Growth (1Y)
    4. Revenue CAGR (Max available years)
    5. EPS Growth
    6. ROE
    7. ROCE
    8. FCF/NP
    9. FCF/Revenue
    10. Debt/Equity
    """
    ticker = ticker_symbol.strip().upper() + ".NS"
    stock = yf.Ticker(ticker)
    info = stock.info
    
    # Helper to safely get values from info
    def get_val(key, default=np.nan):
        val = info.get(key)
        return float(val) if val is not None else default

    # 1. Valuation
    pe = get_val("trailingPE")
    peg = get_val("pegRatio")
    
    # 2. Growth
    rev_growth_1y = get_val("revenueGrowth")
    eps_growth = get_val("earningsGrowth")
    
    # Revenue CAGR
    rev_cagr = np.nan
    try:
        financials = stock.financials
        if financials is not None and not financials.empty and "Total Revenue" in financials.index:
            rev_history = financials.loc["Total Revenue"].dropna()
            if len(rev_history) >= 2:
                latest_rev = rev_history.iloc[0]
                oldest_rev = rev_history.iloc[-1]
                years = len(rev_history) - 1
                if oldest_rev > 0 and years > 0:
                    rev_cagr = (latest_rev / oldest_rev) ** (1 / years) - 1.0
    except Exception:
        pass

    # 3. Quality / Efficiency
    roe = get_val("returnOnEquity")
    
    # ROCE = EBIT / Capital Employed
    roce = np.nan
    try:
        bs = stock.balance_sheet
        financials = stock.financials
        if bs is not None and not bs.empty and financials is not None and not financials.empty:
            total_assets = bs.loc["Total Assets"].iloc[0] if "Total Assets" in bs.index else np.nan
            current_liab = bs.loc["Current Liabilities"].iloc[0] if "Current Liabilities" in bs.index else 0
            ebit = financials.loc["EBIT"].iloc[0] if "EBIT" in financials.index else np.nan
            capital_employed = total_assets - current_liab
            if pd.notna(ebit) and pd.notna(capital_employed) and capital_employed != 0:
                roce = ebit / capital_employed
    except Exception:
        pass
        
    # FCF/NP and FCF/Revenue
    fcf = get_val("freeCashflow")
    net_income = get_val("netIncomeToCommon")
    total_rev = get_val("totalRevenue")
    
    fcf_np = fcf / net_income if (pd.notna(fcf) and pd.notna(net_income) and net_income != 0) else np.nan
    fcf_rev = fcf / total_rev if (pd.notna(fcf) and pd.notna(total_rev) and total_rev != 0) else np.nan

    # 4. Risk
    debt_equity = get_val("debtToEquity")

    return [
        pe, peg, 
        rev_growth_1y, rev_cagr, eps_growth, 
        roe, roce, fcf_np, fcf_rev, 
        debt_equity
    ]

if __name__ == "__main__":
    print("Testing DELHIVERY (Momentum):")
    print(compute_momentum_factors("DELHIVERY"))
    print("\nTesting DELHIVERY (Fundamentals):")
    print(compute_fundamental_factors("DELHIVERY"))
    print("\nTesting DELTACORP (Fundamentals):")
    print(compute_fundamental_factors("DELTACORP"))