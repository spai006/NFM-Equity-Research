"""
Metric computation module for NFM Equity Research.

All metrics are pure functions.
They take primitive numeric inputs and return floats.
Missing / invalid inputs are handled safely.

"""
# ===============================
# FINAL CORE METRICS (LOCKED v1)
# ===============================
# Profitability:
#   roe, roce, net_profit_margin, operating_margin
#
# Growth:
#   revenue_cagr, profit_cagr
#
# Leverage:
#   debt_to_equity, interest_coverage
#
# Cash Flow:
#   operating_cf_ratio, free_cash_flow, fcf_margin
#
# Efficiency:
#   asset_turnover
#
# Stability:
#   earnings_volatility
# ===============================


import numpy as np

# ------------------------
# Helper utilities
# ------------------------

def safe_div(numerator, denominator):
    """Safely divide two numbers, returning NaN if invalid."""
    try:
        if denominator == 0 or denominator is None:
            return np.nan
        return numerator / denominator
    except Exception:
        return np.nan


# ------------------------
# Profitability Metrics
# ------------------------

def roe(net_income, equity):
    """
    Return on Equity.
    Measures profitability relative to shareholder capital.
    """
    return safe_div(net_income, equity)


def roce(ebit, capital_employed):
    """
    Return on Capital Employed.
    Measures efficiency of capital usage.
    """
    return safe_div(ebit, capital_employed)


def net_profit_margin(net_income, revenue):
    """
    Net Profit Margin.
    Indicates how much profit is generated per unit revenue.
    """
    return safe_div(net_income, revenue)


def operating_margin(ebit, revenue):
    """
    Operating Margin.
    Measures core operating profitability.
    """
    return safe_div(ebit, revenue)


# ------------------------
# Growth Metrics
# ------------------------

def revenue_cagr(revenue_start, revenue_end, years):
    """
    Revenue CAGR over given years.
    """
    if years <= 0 or revenue_start <= 0 or revenue_end <= 0:
        return np.nan
    return (revenue_end / revenue_start) ** (1 / years) - 1


def profit_cagr(profit_start, profit_end, years):
    """
    Net Profit CAGR over given years.
    """
    if years <= 0:
        return np.nan
    return (safe_div(profit_end, profit_start) ** (1 / years)) - 1



# ------------------------
# Leverage & Solvency
# ------------------------

def debt_to_equity(total_debt, equity):
    """
    Debt to Equity ratio.
    Measures financial leverage.
    """
    return safe_div(total_debt, equity)


def interest_coverage(ebit, interest_expense):
    """
    Interest Coverage Ratio.
    Ability to service debt.
    """
    return safe_div(ebit, interest_expense)


# ------------------------
# Cash Flow Metrics
# ------------------------

def operating_cf_ratio(cfo, net_income):
    """
    Operating Cash Flow to Net Income.
    Detects earnings quality.
    """
    return safe_div(cfo, net_income)


def free_cash_flow(cfo, capex):
    """
    Free Cash Flow.
    """
    try:
        return cfo - capex
    except Exception:
        return np.nan


def fcf_margin(fcf, revenue):
    """
    Free Cash Flow Margin.
    """
    return safe_div(fcf, revenue)


# ------------------------
# Efficiency Metrics
# ------------------------

def asset_turnover(revenue, total_assets):
    """
    Asset Turnover Ratio.
    Measures revenue generation efficiency.
    """
    return safe_div(revenue, total_assets)


# ------------------------
# Stability & Quality
# ------------------------

def earnings_volatility(std_net_income, mean_net_income):
    """
    Earnings volatility (lower is better).
    Coefficient of variation with safety check.
    """
    if mean_net_income == 0 or mean_net_income is None:
        return np.nan
    return abs(std_net_income) / abs(mean_net_income)

#promoter pledge of shares?




# ------------------------
# Master function (optional convenience)
# ------------------------

def compute_all_metrics(row):
    """
    Compute all metrics for a single company row.
    Expects a dict-like input (e.g., pandas Series).
    """
    metrics = {}

    # Profitability
    metrics["roe"] = roe(row["net_income"], row["equity"])
    metrics["roce"] = roce(row["ebit"], row["capital_employed"])
    metrics["net_margin"] = net_profit_margin(row["net_income"], row["revenue"])
    metrics["operating_margin"] = operating_margin(row["ebit"], row["revenue"])

    # Growth
    metrics["revenue_cagr"] = revenue_cagr(
        row["revenue_3y_ago"], row["revenue"], 3
    )
    metrics["profit_cagr"] = profit_cagr(
        row["profit_3y_ago"], row["net_income"], 3
    )

    # Leverage
    metrics["debt_to_equity"] = debt_to_equity(row["total_debt"], row["equity"])
    metrics["interest_coverage"] = interest_coverage(
        row["ebit"], row["interest_expense"]
    )

    # Cash flow
    metrics["ocf_ratio"] = operating_cf_ratio(row["cfo"], row["net_income"])
    metrics["fcf"] = free_cash_flow(row["cfo"], row["capex"])
    metrics["fcf_margin"] = fcf_margin(metrics["fcf"], row["revenue"])

    # Efficiency
    metrics["asset_turnover"] = asset_turnover(row["revenue"], row["total_assets"])

    return metrics
