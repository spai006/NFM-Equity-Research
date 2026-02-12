# Data Validation Notes

## 1. Data Sanity Checks

### Checks Performed
- **Negative Values**: Verified that `revenue`, `total_assets`, `equity`, `capital_employed` are non-negative.
- **Ratios**: Checked `roe`, `debt_to_equity`, `net_margin` for extreme outliers (e.g., ROE > 500% or < -100%).
- **Missing Values**: Scanned for missing data in critical columns (`ebit`, `roce`, `operating_margin`, `interest_coverage`).
- **Duplicates**: Checked for duplicate `ticker` entries.
- **Zero Values**: Ensured `revenue` and `total_assets` are non-zero.

### Observations
- **Negative Values**: PASS. No negative values found in core financial metrics for the sample set.
- **Ratios**: PASS. All ratios appear within realistic bounds for the sample companies.
  - TCS ROE is ~51%, which is high but valid for IT services.
  - ITC Debt/Equity is remarkably low (~0.004), consistent with its cash-rich status.
- **Missing Values**: FAIL (Warning).
  - **HDFCBANK**: Missing values detected for `ebit`, `roce`, `operating_margin`, and `interest_coverage`. This is expected for banking stocks where EBIT/ROCE are often not standard metrics (Banks use Net Interest Income/ROA), but represents a gap in the standardized schema.
- **Duplicates**: PASS. All tickers are unique.
- **Zero Values**: PASS. All companies have non-zero Revenue and Assets.

## 2. Unstable / Noisy Metrics

- **Revenue CAGR**: Can be misleading if the base year was anomalous (e.g., pandemic lows), artificially inflating growth rates.
- **Free Cash Flow (FCF)**: Highly volatile for capital-intensive sectors (e.g., Telecommunications, Oil & Gas) due to irregular, large-scale capital expenditure cycles.
- **Net Margin**: Sensitive to one-off income or expenses (e.g., asset sales, tax refunds), potentially distorting true operating stability.
- **Debt-to-Equity**: May look artificially high for companies with negative or low equity due to buybacks or accumulated losses, not necessarily indicating distress.

## 3. Assumptions & Limitations

### Assumptions
- **Data Integrity**: Financial data is assumed to be accurate as reported by the data provider/company filings; no independent forensic verification is performed.
- **Standardized Schema**: Generic metrics (e.g., EBIT, EBITDA) are applied across all sectors, assuming reasonable comparability even for specialized sectors like Banking (where Net Interest Income is standard).
- **Recency**: The latest available annual data is treated as the current representation of company fundamentals, potentially ignoring intra-year quarterly shifts.

### Limitations
- **Macro Blindness**: The model does not explicitly adjust for macroeconomic shocks (inflation, interest rate hikes) or regulatory overhauls.
- **Qualitative Gap**: Critical qualitative factors—management quality, corporate governance, and brand strength—are only indirectly captured through financial outcomes.
- **Reporting Lag**: Alerts might differ from real-time events solely due to the time lag between an event and its reflection in quarterly/annual financial disclosures.


