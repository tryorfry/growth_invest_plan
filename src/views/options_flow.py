"""Options Flow scanner for tracking institutional sweeps and unusual volume"""

import streamlit as st
import pandas as pd
from src.data_sources.options_source import OptionsSource

def render_options_flow_page():
    st.title("🌊 Options Flow Scanner")
    st.markdown("Track unusual options activity, institutional sweeps, and 'Smart Money' prints.")
    
    with st.container(border=True):
        st.subheader("⚙️ Scanner Settings")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            ticker = st.text_input("Ticker to Scan", value="NVDA").upper()
        with col2:
            min_vol = st.number_input("Min Volume", min_value=100, max_value=10000, value=1000, step=100)
        with col3:
            min_ratio = st.slider("Min Vol/OI Ratio", 1.0, 10.0, 3.0, step=0.5, help="Volume vs Open Interest. Higher = More unusual")
        with col4:
            run_btn = st.button("🔍 Scan Flow", type="primary", use_container_width=True)
            
    if run_btn and ticker:
        with st.spinner(f"Scanning option chains for {ticker}... (This may take a few seconds)"):
            scanner = OptionsSource()
            results = scanner.scan_unusual_activity(ticker, min_volume=min_vol, vol_oi_ratio=min_ratio)
            
        if not results:
            st.info(f"No unusual options activity found for {ticker} matching the criteria.")
            return
            
        st.success(f"Found {len(results)} unusual prints!")
        
        # Display aggregated metrics
        df = pd.DataFrame(results)
        
        col1, col2, col3 = st.columns(3)
        call_prem = df[df['type'] == 'Call']['premium_est'].sum()
        put_prem = df[df['type'] == 'Put']['premium_est'].sum()
        
        with col1:
            st.metric("Total Call Premium", f"${call_prem:,.0f}", help="Estimated premium spent on bullish trades")
        with col2:
            st.metric("Total Put Premium", f"${put_prem:,.0f}", help="Estimated premium spent on bearish/hedge trades")
        with col3:
            sentiment = "Bullish ⭐" if call_prem > put_prem * 1.5 else "Bearish 🩸" if put_prem > call_prem * 1.5 else "Neutral ⚖️"
            st.metric("Flow Sentiment", sentiment)
            
        st.divider()
        
        # Display the prints
        st.subheader("🔥 Smart Money Prints")
        
        # Format the dataframe for display
        display_df = df.copy()
        
        # Add a visual flag column
        def get_flag(row):
            if row['vol_oi_ratio'] > 10 and row['dte'] <= 14:
                return "🚨 URGENT SWEEP"
            elif row['premium_est'] > 1000000:
                return "🐳 WHALE BLOCK"
            elif row['otm_pct'] > 10:
                return "🎯 LOTO PLAY"
            return "✅ UNUSUAL"
            
        display_df['Signal'] = display_df.apply(get_flag, axis=1)
        
        display_df = display_df[['Signal', 'type', 'strike', 'exp_date', 'dte', 'volume', 'open_interest', 'vol_oi_ratio', 'premium_est', 'otm_pct']]
        
        # Format columns
        display_df.columns = ['Signal', 'Type', 'Strike', 'Expiry', 'DTE', 'Volume', 'OI', 'Vol/OI', 'Est. Premium', 'OTM %']
        
        st.dataframe(
            display_df.style.format({
                'Strike': '${:.2f}',
                'Volume': '{:,}',
                'OI': '{:,}',
                'Vol/OI': '{:.1f}x',
                'Est. Premium': '${:,.0f}',
                'OTM %': '{:.1f}%'
            }).map(lambda x: 'background-color: rgba(0,255,0,0.1); color: green;' if x == 'Call' else 'background-color: rgba(255,0,0,0.1); color: red;' if x == 'Put' else '', subset=['Type']),
            use_container_width=True,
            height=600
        )
