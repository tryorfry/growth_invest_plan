"""Market Pulse page for global metrics"""

import streamlit as st
import pandas as pd
from src.data_sources.macro_source import MacroSource
from src.data_sources.sector_source import SectorSource
import plotly.graph_objects as go

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
    
    # --- Sector Deep Dive ---
    st.divider()
    st.subheader("🎯 Sector Watchlist (Deep Dive)")
    st.markdown("Identify leaders within individual sectors. Ranked by Market Capitalization.")

    from src.data_sources.ticker_scraper import SectorTickerScraper
    scraper = SectorTickerScraper()
    
    # 1. Select Sector (default to top performer of the day if available)
    sector_list = list(SectorTickerScraper.SECTOR_MAPPING.keys())
    default_sector = sector_list[0]
    
    if sector_data:
        # Sort sector_data to find best performer
        sorted_sectors = sorted(sector_data.items(), key=lambda x: x[1], reverse=True)
        if sorted_sectors:
            best_sector = sorted_sectors[0][0]
            if best_sector in sector_list:
                default_sector = best_sector

    col_sel, col_btn = st.columns([0.4, 0.6])
    with col_sel:
        selected_sector = st.selectbox("Drill down into Sector:", sector_list, index=sector_list.index(default_sector))
    
    # 2. Fetch and Render Leaderboard
    with st.spinner(f"Fetching leaders for {selected_sector}..."):
        # Use a session-state buster to allow manual refreshes
        buster = st.session_state.get(f'buster_{selected_sector}', 0)
        top_tickers = scraper.fetch_top_tickers(selected_sector, _cache_buster=buster)
        
    if top_tickers:
        # Check if we are in fallback mode
        is_fallback = any(t.get('is_fallback') for t in top_tickers)
        
        # Action Buttons for the whole batch
        with col_btn:
            st.write("") # Padding
            c_batch, c_reload = st.columns([0.7, 0.3])
            with c_batch:
                batch_btn = st.button(f"🚀 Run Multi-Style Analysis on {selected_sector} Leaders", type="primary", use_container_width=True)
            with c_reload:
                if st.button("🔄 Reload", help="Bypass cache and fetch fresh data from Finviz"):
                    import time
                    st.session_state[f'buster_{selected_sector}'] = time.time()
                    st.rerun()

        # Render Leaderboard as an interactive list
        if is_fallback:
            st.warning("⚠️ **S&P 500 Benchmark Mode**: Live connection to Finviz is currently blocked. Showing verified index leaders.")
            st.markdown(f"### 🏛️ {selected_sector} (S&P 500 Giants)")
        else:
            st.markdown(f"### 🏆 {selected_sector} Leaders")
            
        if batch_btn:
            ticker_string = ",".join([t['ticker'] for t in top_tickers])
            # Direct redirection logic using session state
            st.session_state['ms_report_text'] = ticker_string
            st.session_state['go_to_page'] = '🏁 Multi-Style'
            st.toast(f"Loading {len(top_tickers)} tickers into Multi-Style engine...", icon="🚀")
            import time
            time.sleep(0.5)
            st.rerun()

        # We can't put buttons in a dataframe easily, so we use a loop with columns for the top 15
        # for a crisp UI experience
        for i, t in enumerate(top_tickers[:15]): # Show top 15 with quick actions
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([0.15, 0.45, 0.2, 0.2])
                with c1:
                    st.markdown(f"**{t['ticker']}**")
                with c2:
                    st.caption(f"{t['company']}")
                with c3:
                    if t.get('is_fallback'):
                        st.write("---")
                    else:
                        st.write(f"{t['price']} ({t['change']})")
                with c4:
                    if st.button("Analyze", key=f"mp_ana_{t['ticker']}_{i}", use_container_width=True):
                        st.session_state['main_dash_text'] = t['ticker']
                        st.session_state['go_to_page'] = '🏠 Home'
                        st.rerun()
        
        if len(top_tickers) > 15:
            st.caption(f"... and {len(top_tickers)-15} more leaders below.")
            df_rest = pd.DataFrame(top_tickers[15:])
            # Filter columns to only what exists
            cols_to_show = ['ticker', 'company', 'market_cap']
            if not is_fallback:
                cols_to_show.extend(['price', 'change'])
            
            df_rest = df_rest[cols_to_show]
            df_rest.columns = [c.replace('_', ' ').title() for c in cols_to_show]
            st.dataframe(df_rest, use_container_width=True, hide_index=True)

    else:
        st.info(f"Leaderboard currently unavailable for {selected_sector}. Try again later.")

    st.divider()
    st.subheader("📈 Yield Trend (1 Year)")
    
    # Re-fetch historical macro if needed or use existing
    hist_10y = MacroSource.fetch_historical_macro('10Y_Yield')
    
    if isinstance(hist_10y, pd.DataFrame) and not hist_10y.empty:
        st.line_chart(hist_10y['Close'])
    
    st.divider()
    st.caption("Data provided by Yahoo Finance & Finviz. Yields represent daily closing rates.")
