def evaluate_alerts(company_data, prev_company_data):
    """
    Evaluates monitoring rules against current and previous company data.
    
    Args:
        company_data (dict/Series): Current cycle metrics. Must include 'final_score', 'debt_to_equity', 'cfo'.
        prev_company_data (dict/Series): Previous cycle metrics. Can be None if no history.
        
    Returns:
        list: List of triggered alerts (dicts). Each alert has type, severity, message.
    """
    alerts = []
    
    if prev_company_data is None:
        return alerts

    # --- Rule 1: Score Drop % ---
    current_score = company_data.get('final_score', 0)
    prev_score = prev_company_data.get('final_score', 0)
    
    if prev_score > 0:
        score_change_pct = (current_score - prev_score) / prev_score
        
        # Threshold: > 15% drop triggers alert
        if score_change_pct < -0.15: 
            alerts.append({
                "type": "SCORE_DROP",
                "severity": "HIGH",
                "message": f"Composite score dropped by {abs(score_change_pct):.1%}"
            })

    # --- Rule 2: Debt Spike ---
    current_de = company_data.get('debt_to_equity', 0)
    prev_de = prev_company_data.get('debt_to_equity', 0)
    
    # Threshold: Debt/Equity increased by > 0.5 absolute or > 50% relative if meaningful
    if current_de > prev_de:
        if (current_de - prev_de) > 0.5:
            alerts.append({
                "type": "DEBT_SPIKE",
                "severity": "MEDIUM",
                "message": f"Debt/Equity ratio spiked from {prev_de:.2f} to {current_de:.2f}"
            })

    # --- Rule 3: Cash Flow Collapse ---
    current_cfo = company_data.get('cfo', 0)
    prev_cfo = prev_company_data.get('cfo', 0)
    
    # Logic: CFO was positive, now significantly lower or negative
    # Threshold: Drop > 50%
    if prev_cfo > 0:
        cfo_change_pct = (current_cfo - prev_cfo) / prev_cfo
        if cfo_change_pct < -0.50:
             alerts.append({
                "type": "CASH_FLOW_COLLAPSE",
                "severity": "HIGH",
                "message": f"Operating Cash Flow collapsed by {abs(cfo_change_pct):.1%}"
            })
            
    return alerts

if __name__ == "__main__":
    # Dummy Test
    curr = {'final_score': 8.0, 'debt_to_equity': 1.2, 'cfo': 500}
    prev = {'final_score': 10.0, 'debt_to_equity': 0.6, 'cfo': 1200}
    
    print("Testing Alerts...")
    print(evaluate_alerts(curr, prev))
