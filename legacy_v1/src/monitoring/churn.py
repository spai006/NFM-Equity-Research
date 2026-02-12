def decide_churn(rank, alerts):
    """
    Determines churn action based on rank and alerts.
    
    Args:
        rank (int): Current rank of the company (1-based).
        alerts (list): List of triggered alerts (from alerts.py).
        
    Returns:
        dict: {
            "action": "KEEP" | "REMOVE" | "ADD",
            "reason": str,
            "alerts": list
        }
    """
    decision = {
        "action": "KEEP",
        "reason": f"Rank {rank} within stability zone (exact 50)", # Edge case
        "alerts": alerts
    }
    
    # Rule 1 — Removal: If rank > 50
    if rank > 50:
        decision["action"] = "REMOVE"
        decision["reason"] = f"Rank dropped below threshold (Rank = {rank})"
        return decision
        
    # Rule 2 — Inclusion: If rank <= 50
    if rank <= 50:
        decision["action"] = "ADD"
        decision["reason"] = f"Strong ranking (Rank = {rank})"
        return decision
        
    return decision

def generate_churn_report(company_name, rank, alerts, decision):
    """
    Generates a readable churn report block.
    """
    report = []
    report.append(f"Company: {company_name}")
    report.append(f"Action: {decision['action']}")
    report.append(f"Rank: {rank}")
    
    if alerts:
        report.append("Triggered Alerts:")
        for alert in alerts:
            severity = alert.get('severity', 'Unknown')
            msg = alert.get('type', 'ALERT')
            report.append(f"- {msg} ({severity})")
    else:
        report.append("Triggered Alerts: None")
        
    report.append("Reason:")
    report.append(decision['reason'])
    report.append("-" * 20)
    
    return "\n".join(report)

if __name__ == "__main__":
    print("Testing Churn Logic...")
    
    # Test Report Generation
    test_alerts = [{"type": "SCORE_DROP", "severity": "HIGH"}, {"type": "CASH_FLOW_COLLAPSE", "severity": "MEDIUM"}]
    decision = decide_churn(82, test_alerts)
    
    report_text = generate_churn_report("XYZ Ltd", 82, test_alerts, decision)
    print("\n--- Sample Report ---")
    print(report_text)
    
    # Save dummy report
    from config import settings
    log_path = os.path.join(settings.DATA_DIR, 'reports', 'churn_log.md')
    
    with open(log_path, 'w') as f:
        f.write("# Churn Log (Sample)\n\n")
        f.write(report_text)
        f.write("\n")
    print(f"\nSaved sample log to {log_path}")
