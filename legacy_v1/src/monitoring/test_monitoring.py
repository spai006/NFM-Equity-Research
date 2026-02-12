import alerts
import churn

def run_sanity_test():
    print("=== STARTING SANITY TEST ===\n")

    # 1. Define Dummy Data
    companies = [
        {
            "name": "Stable Corp",
            "prev": {"final_score": 8.0, "debt_to_equity": 0.5, "cfo": 1000},
            "curr": {"final_score": 8.1, "debt_to_equity": 0.5, "cfo": 1050},
            "rank": 10
        },
        {
            "name": "Collapsing Ltd",
            "prev": {"final_score": 9.0, "debt_to_equity": 0.8, "cfo": 2000},
            "curr": {"final_score": 7.2, "debt_to_equity": 1.5, "cfo": 800}, # Score drop 20%, Debt up 0.7, CFO drop 60%
            "rank": 65
        },
        {
            "name": "Improving Inc",
            "prev": {"final_score": 6.0, "debt_to_equity": 1.2, "cfo": 500},
            "curr": {"final_score": 7.5, "debt_to_equity": 1.0, "cfo": 600},
            "rank": 25
        }
    ]

    for co in companies:
        print(f"Processing {co['name']} (Rank {co['rank']})...")
        
        # 2. Run Alerts
        triggered_alerts = alerts.evaluate_alerts(co['curr'], co['prev'])
        
        # 3. Decisions Churn
        decision = churn.decide_churn(co['rank'], triggered_alerts)
        
        # 4. Generate Report
        report = churn.generate_churn_report(co['name'], co['rank'], triggered_alerts, decision)
        
        print(report)
        print("\n")
        
    print("=== TEST COMPLETE ===")

if __name__ == "__main__":
    run_sanity_test()
