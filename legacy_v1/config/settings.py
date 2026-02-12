import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DATA_PATH = os.path.join(DATA_DIR, 'raw')

# Market Config
# PROCESSED DATA PATH
PROCESSED_DATA_PATH = os.path.join(DATA_DIR, 'processed', 'features.csv')
MARKET_SUFFIX = '.NS'  # NSE stocks
START_DATE = '2020-01-01'

# Metrics Schema (Required Fields for NFM Model)
REQUIRED_FIELDS = [
    # Profitability
    "net_income",
    "equity",
    "ebit",
    "capital_employed",
    "revenue",
    
    # Growth (Historical)
    "revenue_3y_ago",
    "profit_3y_ago",
    
    # Leverage
    "total_debt",
    "interest_expense",
    
    # Cash Flow
    "cfo",       # Operating Cash Flow
    "capex",     # Capital Expenditure
    
    # Efficiency
    "total_assets"
]

# Yahoo Finance Field Mapping
# Key: Internal Field, Value: Yahoo Finance DataFrame Index (row literal)
YAHOO_MAPPING = {
    "net_income": ["Net Income", "Net Income Common Stockholders"],
    "equity": ["Stockholders Equity", "Total Stockholder Equity"],
    "ebit": ["EBIT", "Operating Income", "EBITDA"], # Fallback chain
    "revenue": ["Total Revenue", "Operating Revenue"],
    "total_debt": ["Total Debt"],
    "interest_expense": ["Interest Expense", "Interest Paid"],
    "cfo": ["Operating Cash Flow", "Total Cash From Operating Activities"],
    "capex": ["Capital Expenditure", "Total Capitalization"],
    "total_assets": ["Total Assets"],
    "current_liabilities": ["Current Liabilities", "Total Current Liabilities"] # For Capital Employed calc
}

# Scoring Weights
# Positive weights = higher is better.
# For metrics where lower is better (Debt/Equity), Scorer will handle inversion before applying weight.
SCORING_WEIGHTS = {
    # Profitability (35 points)
    "roe": 15.0,
    "roce": 10.0,
    "net_margin": 5.0,
    "operating_margin": 5.0,
    
    # Growth (25 points)
    "revenue_cagr": 15.0,
    "profit_cagr": 10.0,
    
    # Cash Flow (20 points)
    "ocf_ratio": 5.0,
    "fcf_margin": 15.0,
    
    # Leverage (10 points) - Scorer inverts these ranks if Lower is Better
    "debt_to_equity": 5.0,
    "interest_coverage": 5.0,
    
    # Efficiency & Stability (10 points)
    "asset_turnover": 5.0,
    "earnings_volatility": 5.0
}

# Metrics where lower values are better (Rank Inversion)
LOWER_IS_BETTER = [
    "debt_to_equity",
    "earnings_volatility"
]

