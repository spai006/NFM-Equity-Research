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
    

if __name__ == "__main__":
    print("Testing DELHIVERY:")
    print(compute_momentum_factors("DELHIVERY"))
    print("\nTesting DELTACORP:")
    print(compute_momentum_factors("DELTACORP"))