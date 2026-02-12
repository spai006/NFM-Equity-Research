
def generate_justification_prompt(company_row, rank):
    """
    Generates a prompt for the LLM to justify the selection of this company.
    
    Args:
        company_row (pd.Series or dict): The row containing company metrics.
        rank (int): The rank of the company in the Top 50.
        
    Returns:
        str: The full prompt text.
    """
    
    # Helper to format numbers cleanly
    def fmt(val, is_percent=False):
        try:
            if val is None or val != val: # Nan check
                return "N/A"
            if is_percent:
                return f"{val * 100:.1f}%"
            return f"{val:.2f}"
        except:
            return "N/A"

    ticker = company_row.get('ticker', 'Unknown')
    roe = fmt(company_row.get('roe'), True)
    roce = fmt(company_row.get('roce'), True)
    sales_growth = fmt(company_row.get('revenue_cagr'), True)
    profit_growth = fmt(company_row.get('profit_cagr'), True)
    debt_equity = fmt(company_row.get('debt_to_equity'))
    fcf_margin = fmt(company_row.get('fcf_margin'), True)
    
    prompt = f"""
You are a top-tier equity research analyst for the Indian Stock Market.

**Task**: Write a concise, high-impact investment thesis for **{ticker}** (Rank #{rank} in our Top 50 Fundamental Model).

**Quantitative Profile**:
- **Profitability**: ROE: {roe}, ROCE: {roce}
- **Growth (3Y CAGR)**: Sales: {sales_growth}, Profit: {profit_growth}
- **Financial Health**: Debt/Equity: {debt_equity}
- **Cash Flow**: FCF Margin: {fcf_margin}

**Instructions**:
1. **Headline**: Start with a catchy 1-sentence hook about why this company is a winner.
2. **Analysis**: Briefly synthesis the metrics. Is it a "Growth Machine" (high CAGR) or a "Cash Cow" (high ROCE/FCF)?
3. **Verdict**: Justify its inclusion in the Top 50.

**Output Format**: 
Plain text, max 3-4 sentences. Professional tone.
"""
    return prompt.strip()

def generate_churn_prompt(company_row, decision, rank, prev_rank=None):
    """
    Generates a prompt for explaining churn decisions (Add/Remove).
    
    Args:
        company_row (pd.Series): Company metrics
        decision (str): 'ADD' or 'REMOVE'
        rank (int): Current rank
        prev_rank (int, optional): Previous rank
    """
    ticker = company_row.get('ticker', 'Unknown')
    
    # Construct a context string of key metrics to help the LLM find the cause
    metrics_context = (
        f"ROE: {company_row.get('roe', 0)*100:.1f}%, "
        f"RevGrowth: {company_row.get('revenue_cagr', 0)*100:.1f}%, "
        f"Debt/Eq: {company_row.get('debt_to_equity', 0):.2f}, "
        f"Score: {company_row.get('final_score', 0):.1f}"
    )

    if decision == "REMOVE":
        return f"""
You are a Portfolio Manager.
**Decision**: REMOVE **{ticker}** from Top 50.
**Current Status**: Rank fell to #{rank} (Threshold is Top 50).
**Metrics**: {metrics_context}

**Task**: 
Explain in 1 strict sentence why this company's fundamentals have deteriorated or why it is no longer elite. 
Focus on the weak metrics relative to the dropped rank.
"""
    
    elif decision == "ADD":
        return f"""
You are a Portfolio Manager.
**Decision**: ADD **{ticker}** to Top 50.
**Current Status**: Rank surged to #{rank}.
**Metrics**: {metrics_context}

**Task**:
Explain in 1 strict sentence why this company is a strong new addition. 
Focus on the improved or superior metrics.
"""
    return ""
