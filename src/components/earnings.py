import streamlit as st
import pandas as pd
from src.analyzer import StockAnalysis

def render_earnings_analysis_section(analysis: StockAnalysis):
    """Render historical earnings gap analysis and risk magnitude"""
    st.subheader("📊 Earnings Gap Analysis")
    
    if not analysis.earnings_history:
        st.info("Historical earnings gap data is currently unavailable for this ticker or could not be fetched.")
        return
    
    # Summary Metrics for Risk
    risk_col1, risk_col2, risk_col3 = st.columns(3)
    
    with risk_col1:
        risk_val = analysis.projected_gap_risk or 0.0
        st.metric(
            "Projected Gap Risk", 
            f"{risk_val:.2f}%", 
            help="Average magnitude of the absolute price gap on earnings day (Expected Move)."
        )
    
    with risk_col2:
        # Calculate consistency/volatility of gaps
        if analysis.earnings_history:
            max_gap = max([abs(e.get("t0_return", 0)) for e in analysis.earnings_history])
            st.metric("Max Historical Gap", f"{max_gap:.2f}%")
            
    with risk_col3:
        # Average T+1 drift
        avg_drift = sum([e.get("t0_return", 0) for e in analysis.earnings_history]) / len(analysis.earnings_history)
        st.metric("Avg Hist. Reaction", f"{avg_drift:+.2f}%", help="Simple average of past reactions (shows if stock leans bullish/bearish on earnings).")

    # Historical Table
    st.markdown("**Recent Quarterly Reactions (Last 1 Year)**")
    
    # Prepare data for table
    table_data = []
    for event in analysis.earnings_history[:4]: # Show last 4 (1 year)
        gap = event.get("t0_return", 0)
        gap_formatted = f"{gap:+.2f}%"
        
        # Color coding for the gap in markdown
        color = "green" if gap > 0 else "red" if gap < 0 else "white"
        
        table_data.append({
            "Date": event.get("date", "N/A"),
            "Reaction Gap": f":{color}[{gap_formatted}]",
            "EPS Est.": event.get("eps_estimate", "N/A"),
            "EPS Act.": event.get("eps_reported", "N/A"),
            "Result": "✅ Beat" if event.get("beat") else "❌ Miss/Meet"
        })
    
    if table_data:
        st.table(pd.DataFrame(table_data))
    else:
        st.info("Insufficient historical data for gap analysis table.")
