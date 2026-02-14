"""Market Pulse page for global metrics"""

import streamlit as st
import pandas as pd
from src.data_sources.macro_source import MacroSource

def render_market_pulse_page():
    st.title("🌍 Market Pulse")
    st.markdown("Global market indicators and macro context for your investment decisions.")
    
    # Fetch Data
    with st.spinner("Fetching global market data..."):
        macro_data = MacroSource.fetch_macro_data()
    
    if not macro_data:
        st.error("Could not fetch market pulse data. Please check your internet connection.")
        return

    # Metric Row 1: Interest Rates
    st.subheader("🏦 Interest Rates & Yields")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        val = macro_data.get('10Y_Yield')
        if val:
            st.metric("US 10Y Yield", f"{val['value']:.2f}%", f"{val['pct_change']:+.2f}%")
    
    with col2:
        val = macro_data.get('5Y_Yield')
        if val:
            st.metric("US 5Y Yield", f"{val['value']:.2f}%", f"{val['pct_change']:+.2f}%")
            
    with col3:
        val = macro_data.get('Short_Yield')
        if val:
            st.metric("US 3M Yield", f"{val['value']:.2f}%", f"{val['pct_change']:+.2f}%")
            
    with col4:
        spread = macro_data.get('Yield_Spread')
        if spread:
            color = "normal" if spread['value'] > 0 else "inverse"
            st.metric(spread['label'], f"{spread['value']:.2f}%", help="Inverted yield curve (negative) often precedes recession.")

    # Metric Row 2: Risk & Multi-Asset
    st.subheader("📉 Risk & Market Sentiment")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        val = macro_data.get('VIX')
        if val:
            st.metric("VIX (Fear Index)", f"{val['value']:.2f}", f"{val['pct_change']:+.2f}%", delta_color="inverse")
            
    with col2:
        val = macro_data.get('SPY')
        if val:
            st.metric("S&P 500 (SPY)", f"${val['value']:.2f}", f"{val['pct_change']:+.2f}%")
            
    with col3:
        val = macro_data.get('Dollar_Index')
        if val:
            st.metric("US Dollar Index", f"{val['value']:.2f}", f"{val['pct_change']:+.2f}%")

    # Historical Yield Trends
    st.divider()
    st.subheader("📊 Sector Performance Heatmap (1D)")
    
    with st.spinner("Calculating sector trends..."):
        sector_data = MacroSource.fetch_sector_data()
        
    if sector_data:
        # Prepare data for plotting
        df_sector = pd.DataFrame(list(sector_data.items()), columns=['Sector', 'Performance'])
        df_sector = df_sector.sort_values('Performance', ascending=True)
        
        # Color coding: Green for positive, Red for negative
        colors = ['red' if x < 0 else 'green' for x in df_sector['Performance']]
        
        import plotly.graph_objects as go
        fig = go.Figure(go.Bar(
            x=df_sector['Performance'],
            y=df_sector['Sector'],
            orientation='h',
            marker_color=colors,
            text=[f"{x:+.2f}%" for x in df_sector['Performance']],
            textposition='auto',
        ))
        
        fig.update_layout(
            title="Daily Performance (%)",
            xaxis_title="Change %",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    st.subheader("📈 Yield Trend (1 Year)")
    
    # Re-fetch historical macro if needed or use existing
    print(f"DEBUG: Available MacroSource methods: {dir(MacroSource)}")
    
    if hasattr(MacroSource, 'fetch_historical_macro'):
        hist_10y = MacroSource.fetch_historical_macro('10Y_Yield')
        
        if isinstance(hist_10y, pd.DataFrame) and not hist_10y.empty:
            st.line_chart(hist_10y['Close'])
    else:
        st.error("DEBUG: fetch_historical_macro method missing from MacroSource class.")
    
    st.divider()
    st.caption("Data provided by Yahoo Finance. Yields represent daily closing rates.")
