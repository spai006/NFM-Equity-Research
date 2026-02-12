"""
Streamlit Dashboard for Fundamental Model Analysis
Phase 4 - Presentation Layer

This dashboard provides an interactive interface to explore:
- Top 50 companies identified by the fundamental model
- Company scores and metrics
- Alert monitoring
- Churn analysis
"""

import streamlit as st
import pandas as pd
import os
from pathlib import Path
from datetime import datetime, timedelta
import random


# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

@st.cache_data
def load_top_50_data():
    """
    Load Top-50 data from CSV file.
    
    Returns:
        pd.DataFrame: Top 50 companies with processed data
    """
    # Construct path to data file
    base_path = Path(__file__).parent.parent.parent
    data_path = base_path / "data" / "reports" / "top_50.csv"
    
    if not data_path.exists():
        st.error(f"❌ Data file not found: {data_path}")
        return pd.DataFrame()
    
    try:
        # Load the CSV
        df = pd.read_csv(data_path)
        
        # Process data for display
        df_display = process_top_50_data(df)
        
        return df_display
    
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return pd.DataFrame()


def process_top_50_data(df):
    """
    Process raw Top-50 data into display format.
    
    Args:
        df: Raw dataframe from CSV
        
    Returns:
        pd.DataFrame: Processed dataframe ready for display
    """
    # Select and rename columns for display
    display_df = pd.DataFrame()
    
    # Add rank (1-indexed)
    display_df['Rank'] = range(1, min(51, len(df) + 1))
    
    # Company name (ticker)
    display_df['Company'] = df['ticker'].head(50)
    
    # Composite Score (rounded to 2 decimals)
    display_df['Score'] = df['final_score'].head(50).round(2)
    
    # Key strengths - derive from top scoring metrics
    display_df['Key Strengths'] = df.head(50).apply(identify_strengths, axis=1)
    
    # Alert count - for now, simulate based on debt and score
    # In production, this would come from actual alert evaluation
    display_df['Alert Count'] = df.head(50).apply(calculate_alert_count, axis=1)
    
    # Add alert status (Yes/No)
    display_df['Has Alerts'] = display_df['Alert Count'].apply(lambda x: '⚠️ Yes' if x > 0 else '✅ No')
    
    return display_df


def identify_strengths(row):
    """
    Identify top strengths for a company based on scores.
    
    Args:
        row: DataFrame row with company metrics
        
    Returns:
        str: Comma-separated list of strengths
    """
    strengths = []
    
    # Check profitability
    if row.get('roe', 0) > 0.20:  # ROE > 20%
        strengths.append('High ROE')
    if row.get('roce', 0) > 0.25:  # ROCE > 25%
        strengths.append('High ROCE')
    
    # Check growth
    if row.get('revenue_cagr', 0) > 0.15:  # Revenue CAGR > 15%
        strengths.append('Strong Growth')
    
    # Check financial health
    if row.get('debt_to_equity', 1) < 0.3:  # Low debt
        strengths.append('Low Debt')
    
    # Check cash generation
    if row.get('fcf_margin', 0) > 0.10:  # FCF Margin > 10%
        strengths.append('Strong FCF')
    
    return ', '.join(strengths[:3]) if strengths else 'Balanced Profile'


def calculate_alert_count(row):
    """
    Calculate number of alerts for a company.
    This is a simplified version - in production, use actual alert evaluation.
    
    Args:
        row: DataFrame row with company metrics
        
    Returns:
        int: Number of alerts
    """
    alert_count = 0
    
    # High debt alert
    if row.get('debt_to_equity', 0) > 1.0:
        alert_count += 1
    
    # Low score alert (if in top 50 but score is relatively low)
    if row.get('final_score', 10) < 6.0:
        alert_count += 1
    
    # Negative FCF alert
    if row.get('fcf_margin', 0) < 0:
        alert_count += 1
    
    return alert_count


def generate_alerts_from_data(df):
    """
    Generate alert log from Top 50 data.
    This simulates what would come from Phase 3 alert monitoring.
    
    Args:
        df: DataFrame with Top 50 data and raw metrics
        
    Returns:
        pd.DataFrame: Alert log with Company, Alert Type, Severity, Date, Message
    """
    alerts_list = []
    
    # Get current date for alerts
    current_date = datetime.now()
    
    for idx, row in df.iterrows():
        company = row['ticker']
        
        # Alert 1: High Debt
        debt_ratio = row.get('debt_to_equity', 0)
        if debt_ratio > 1.0:
            severity = 'HIGH' if debt_ratio > 2.0 else 'MEDIUM'
            alerts_list.append({
                'Company': company,
                'Alert Type': 'DEBT_SPIKE',
                'Severity': severity,
                'Date': (current_date - timedelta(days=random.randint(0, 7))).strftime('%Y-%m-%d'),
                'Message': f'Debt/Equity ratio at {debt_ratio:.2f}'
            })
        
        # Alert 2: Negative FCF
        fcf_margin = row.get('fcf_margin', 0)
        if fcf_margin < 0:
            alerts_list.append({
                'Company': company,
                'Alert Type': 'NEGATIVE_FCF',
                'Severity': 'HIGH',
                'Date': (current_date - timedelta(days=random.randint(0, 5))).strftime('%Y-%m-%d'),
                'Message': f'Free Cash Flow margin is negative ({fcf_margin:.1%})'
            })
        
        # Alert 3: Low Score (relative to Top 50)
        score = row.get('final_score', 10)
        if score < 6.0:
            alerts_list.append({
                'Company': company,
                'Alert Type': 'SCORE_DROP',
                'Severity': 'MEDIUM',
                'Date': (current_date - timedelta(days=random.randint(0, 10))).strftime('%Y-%m-%d'),
                'Message': f'Composite score below threshold ({score:.2f})'
            })
        
        # Alert 4: Low Profitability
        roe = row.get('roe', 0)
        if roe < 0.10 and roe > 0:  # Positive but low
            alerts_list.append({
                'Company': company,
                'Alert Type': 'LOW_PROFITABILITY',
                'Severity': 'LOW',
                'Date': (current_date - timedelta(days=random.randint(0, 14))).strftime('%Y-%m-%d'),
                'Message': f'ROE below 10% ({roe:.1%})'
            })
        
        # Alert 5: Negative Growth
        revenue_cagr = row.get('revenue_cagr', 0)
        if revenue_cagr < 0:
            alerts_list.append({
                'Company': company,
                'Alert Type': 'NEGATIVE_GROWTH',
                'Severity': 'MEDIUM',
                'Date': (current_date - timedelta(days=random.randint(0, 7))).strftime('%Y-%m-%d'),
                'Message': f'Revenue declining ({revenue_cagr:.1%} CAGR)'
            })
    
    # Convert to DataFrame
    if alerts_list:
        alerts_df = pd.DataFrame(alerts_list)
        # Sort by date (most recent first) and severity
        severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        alerts_df['severity_rank'] = alerts_df['Severity'].map(severity_order)
        alerts_df = alerts_df.sort_values(['severity_rank', 'Date'], ascending=[True, False])
        alerts_df = alerts_df.drop('severity_rank', axis=1)
        return alerts_df
    else:
        return pd.DataFrame(columns=['Company', 'Alert Type', 'Severity', 'Date', 'Message'])


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def display_top_50_table(df):
    """
    Display the Top 50 companies table with visual highlighting.
    
    Args:
        df: DataFrame with Top 50 data
    """
    st.markdown("### 🏆 Top 50 Fundamentally Strong Companies")
    
    if df.empty:
        st.warning("No data available to display.")
        return
    
    # Create a copy for styling
    styled_df = df.copy()
    
    # Prepare display columns
    display_cols = ['Rank', 'Company', 'Score', 'Key Strengths', 'Has Alerts']
    
    # Apply custom styling using Streamlit's dataframe with conditional formatting
    def highlight_alerts(row):
        """Apply row-wise styling based on alert status"""
        if '⚠️' in str(row['Has Alerts']):
            return ['background-color: #fff3cd; color: black'] * len(row)  # Light yellow for alerts, black font
        return [''] * len(row)
    
    # Display the table
    st.dataframe(
        styled_df[display_cols].style.apply(highlight_alerts, axis=1),
        use_container_width=True,
        height=600,
        hide_index=True
    )
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Companies", len(df))
    
    with col2:
        companies_with_alerts = (df['Alert Count'] > 0).sum()
        st.metric("Companies with Alerts", companies_with_alerts)
    
    with col3:
        avg_score = df['Score'].mean()
        st.metric("Average Score", f"{avg_score:.2f}")
    
    with col4:
        top_score = df['Score'].max()
        st.metric("Highest Score", f"{top_score:.2f}")
    
    # Add company drill-down section
    st.markdown("---")
    st.markdown("### 🔍 Company Details")
    st.markdown("Select a company to view detailed information:")
    
    # Company selector
    company_list = sorted(df['Company'].tolist())
    selected_company = st.selectbox(
        "Choose a company:",
        options=company_list,
        index=0,
        help="Select a company to view detailed analysis"
    )
    
    if selected_company:
        display_company_details(selected_company, df)


def display_company_details(company_ticker, top_50_df):
    """
    Display detailed information for a selected company.
    
    Args:
        company_ticker: Company ticker symbol
        top_50_df: DataFrame with Top 50 display data
    """
    # Load raw data for detailed metrics
    base_path = Path(__file__).parent.parent.parent
    data_path = base_path / "data" / "reports" / "top_50.csv"
    
    if not data_path.exists():
        st.error("Unable to load detailed company data.")
        return
    
    raw_df = pd.read_csv(data_path)
    company_data = raw_df[raw_df['ticker'] == company_ticker]
    
    if company_data.empty:
        st.warning(f"No data found for {company_ticker}")
        return
    
    company_row = company_data.iloc[0]
    display_row = top_50_df[top_50_df['Company'] == company_ticker].iloc[0]
    
    # Company header
    st.markdown(f"## 📊 {company_ticker}")
    rank = display_row['Rank']
    st.markdown(f"**Rank:** #{rank} in Top 50")
    
    st.markdown("---")
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["📈 Score Breakdown", "⚠️ Active Alerts", "🔄 Churn Status"])
    
    with tab1:
        st.markdown("### Composite Score Analysis")
        
        # Overall score
        col1, col2 = st.columns([1, 2])
        with col1:
            score = company_row.get('final_score', 0)
            st.metric("Composite Score", f"{score:.2f}", help="Overall fundamental strength score")
        
        with col2:
            st.markdown("**Key Strengths:**")
            st.info(display_row['Key Strengths'])
        
        st.markdown("---")
        st.markdown("#### Score Components")
        
        # Score breakdown in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("**Profitability**")
            roe = company_row.get('roe', 0)
            roce = company_row.get('roce', 0)
            st.metric("ROE", f"{roe:.1%}")
            st.metric("ROCE", f"{roce:.1%}")
        
        with col2:
            st.markdown("**Growth**")
            rev_cagr = company_row.get('revenue_cagr', 0)
            profit_cagr = company_row.get('profit_cagr', 0)
            st.metric("Revenue CAGR", f"{rev_cagr:.1%}" if pd.notna(rev_cagr) else "N/A")
            st.metric("Profit CAGR", f"{profit_cagr:.1%}" if pd.notna(profit_cagr) else "N/A")
        
        with col3:
            st.markdown("**Financial Health**")
            debt_equity = company_row.get('debt_to_equity', 0)
            st.metric("Debt/Equity", f"{debt_equity:.2f}")
            
            # Color code based on debt level
            if debt_equity < 0.5:
                st.success("✅ Low Debt")
            elif debt_equity < 1.0:
                st.info("ℹ️ Moderate Debt")
            else:
                st.warning("⚠️ High Debt")
        
        with col4:
            st.markdown("**Cash Generation**")
            fcf_margin = company_row.get('fcf_margin', 0)
            st.metric("FCF Margin", f"{fcf_margin:.1%}" if pd.notna(fcf_margin) else "N/A")
            
            if fcf_margin > 0.10:
                st.success("✅ Strong FCF")
            elif fcf_margin > 0:
                st.info("ℹ️ Positive FCF")
            else:
                st.error("❌ Negative FCF")
    
    with tab2:
        st.markdown("### Active Alerts for this Company")
        
        # Generate alerts for this specific company
        company_alerts = generate_alerts_from_data(company_data)
        
        if company_alerts.empty:
            st.success("✅ No active alerts for this company!")
            st.markdown("This company is performing well across all monitored metrics.")
        else:
            st.warning(f"⚠️ {len(company_alerts)} alert(s) detected")
            
            # Display each alert
            for idx, alert in company_alerts.iterrows():
                severity = alert['Severity']
                alert_type = alert['Alert Type']
                message = alert['Message']
                date = alert['Date']
                
                # Color based on severity
                if severity == 'HIGH':
                    st.error(f"🔴 **{alert_type}** (High Severity)")
                elif severity == 'MEDIUM':
                    st.warning(f"🟡 **{alert_type}** (Medium Severity)")
                else:
                    st.info(f"🔵 **{alert_type}** (Low Severity)")
                
                st.markdown(f"- **Issue:** {message}")
                st.markdown(f"- **Detected:** {date}")
                st.markdown("---")
    
    with tab3:
        st.markdown("### Churn Decision Status")
        
        # Simulate churn decision logic
        # In production, this would come from actual churn tracking
        score = company_row.get('final_score', 0)
        alert_count = display_row['Alert Count']
        
        st.markdown("#### Current Status")
        
        # Determine churn risk
        if score >= 7.0 and alert_count == 0:
            st.success("✅ **STABLE** - Company is secure in Top 50")
            churn_risk = "Low"
            recommendation = "Continue monitoring. No action needed."
        elif score >= 6.0 and alert_count <= 2:
            st.info("ℹ️ **WATCH** - Company is stable but should be monitored")
            churn_risk = "Medium"
            recommendation = "Monitor closely for any deterioration in metrics."
        else:
            st.warning("⚠️ **AT RISK** - Company may be removed from Top 50")
            churn_risk = "High"
            recommendation = "Review fundamentals. Consider for removal if conditions worsen."
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Churn Risk", churn_risk)
            st.metric("Current Score", f"{score:.2f}")
        
        with col2:
            st.metric("Active Alerts", alert_count)
            
            # Score threshold
            threshold = 6.0
            if score >= threshold:
                st.metric("Above Threshold", f"+{score - threshold:.2f}")
            else:
                st.metric("Below Threshold", f"{score - threshold:.2f}", delta_color="inverse")
        
        st.markdown("---")
        st.markdown("#### Recommendation")
        st.info(recommendation)
        
        # Last decision (simulated)
        st.markdown("---")
        st.markdown("#### Decision History")
        
        if rank <= 10:
            st.success(f"**Last Decision:** RETAIN (Top 10 performer)")
            st.caption("Decision Date: 2025-12-15 | Reason: Consistently strong fundamentals")
        elif rank <= 30:
            st.info(f"**Last Decision:** RETAIN (Solid performer)")
            st.caption("Decision Date: 2025-12-15 | Reason: Meets all retention criteria")
        else:
            st.warning(f"**Last Decision:** RETAIN (Under review)")
            st.caption("Decision Date: 2025-12-15 | Reason: Score above threshold but monitoring required")


def display_alerts_panel(alerts_df):
    """
    Display the Active Alerts panel with filtering.
    
    Args:
        alerts_df: DataFrame with alert data
    """
    st.markdown("### ⚠️ Active Alerts")
    
    if alerts_df.empty:
        st.success("✅ No active alerts! All companies are performing well.")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Alerts", len(alerts_df))
    
    with col2:
        high_alerts = (alerts_df['Severity'] == 'HIGH').sum()
        st.metric("High Severity", high_alerts, delta=None, delta_color="inverse")
    
    with col3:
        medium_alerts = (alerts_df['Severity'] == 'MEDIUM').sum()
        st.metric("Medium Severity", medium_alerts)
    
    with col4:
        low_alerts = (alerts_df['Severity'] == 'LOW').sum()
        st.metric("Low Severity", low_alerts)
    
    st.markdown("---")
    
    # Severity filter
    col_filter1, col_filter2 = st.columns([1, 3])
    
    with col_filter1:
        severity_options = ['All'] + sorted(alerts_df['Severity'].unique().tolist(), 
                                           key=lambda x: {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}.get(x, 3))
        selected_severity = st.selectbox(
            "Filter by Severity:",
            options=severity_options,
            index=0
        )
    
    # Filter data
    if selected_severity != 'All':
        filtered_alerts = alerts_df[alerts_df['Severity'] == selected_severity].copy()
    else:
        filtered_alerts = alerts_df.copy()
    
    # Display count after filtering
    with col_filter2:
        st.info(f"📊 Showing **{len(filtered_alerts)}** alert(s)")
    
    # Display alerts table with color coding
    if not filtered_alerts.empty:
        def highlight_severity(row):
            """Apply row-wise styling based on severity"""
            if row['Severity'] == 'HIGH':
                return ['background-color: #f8d7da'] * len(row)  # Light red
            elif row['Severity'] == 'MEDIUM':
                return ['background-color: #fff3cd'] * len(row)  # Light yellow
            elif row['Severity'] == 'LOW':
                return ['background-color: #d1ecf1'] * len(row)  # Light blue
            return [''] * len(row)
        
        # Add severity icons
        def add_severity_icon(severity):
            if severity == 'HIGH':
                return '🔴 HIGH'
            elif severity == 'MEDIUM':
                return '🟡 MEDIUM'
            elif severity == 'LOW':
                return '🔵 LOW'
            return severity
        
        display_alerts = filtered_alerts.copy()
        display_alerts['Severity'] = display_alerts['Severity'].apply(add_severity_icon)
        
        st.dataframe(
            display_alerts.style.apply(highlight_severity, axis=1),
            use_container_width=True,
            height=400,
            hide_index=True
        )
    else:
        st.info("No alerts match the selected filter.")


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    
    # Configure page settings
    st.set_page_config(
        page_title="Fundamental Model Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # ========================================================================
    # SIDEBAR NAVIGATION
    # ========================================================================
    
    with st.sidebar:
        st.title("🧭 Navigation")
        st.markdown("---")
        
        # Simple navigation with radio buttons
        view = st.radio(
            "Select View:",
            options=["Top 50", "Alerts"],
            index=0,
            help="Switch between different dashboard views"
        )
        
        st.markdown("---")
        
        # Additional info in sidebar
        st.markdown("### 📊 Dashboard Info")
        st.info("""
        **Fundamental Model Dashboard**
        
        - View top-performing companies
        - Monitor active alerts
        - Track risk indicators
        """)
        
        st.markdown("---")
        st.caption("Phase 4 - Presentation Layer")
    
    # ========================================================================
    # MAIN CONTENT AREA
    # ========================================================================
    
    # Main heading
    st.title("📊 Fundamental Model Dashboard")
    
    # Load data once (used by both views)
    with st.spinner("Loading data..."):
        top_50_df = load_top_50_data()
        
        # Load raw data for alerts
        base_path = Path(__file__).parent.parent.parent
        data_path = base_path / "data" / "reports" / "top_50.csv"
        
        if data_path.exists():
            raw_df = pd.read_csv(data_path)
            alerts_df = generate_alerts_from_data(raw_df.head(50))
        else:
            alerts_df = pd.DataFrame()
    
    # ========================================================================
    # VIEW SWITCHING
    # ========================================================================
    
    if view == "Top 50":
        # TOP 50 VIEW
        st.markdown("### 📈 Top 50 Companies Overview")
        st.markdown("Explore the fundamentally strongest companies identified by our model.")
        st.markdown("---")
        
        if not top_50_df.empty:
            display_top_50_table(top_50_df)
        else:
            st.error("❌ Unable to load Top 50 data. Please check the data files.")
    
    elif view == "Alerts":
        # ALERTS VIEW
        st.markdown("### ⚠️ Active Alerts Overview")
        st.markdown("Monitor risk indicators and issues across the Top 50 companies.")
        st.markdown("---")
        
        if not alerts_df.empty or top_50_df.empty:
            display_alerts_panel(alerts_df)
        else:
            st.warning("⚠️ Unable to generate alerts - data file not found.")
    
    # ========================================================================
    # FOOTER
    # ========================================================================
    
    st.markdown("---")
    st.caption("📈 Fundamental Model Dashboard | Data updated from Phase 2/3 pipeline")


if __name__ == "__main__":
    main()
