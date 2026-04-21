"""Market Pulse page for global metrics"""

import streamlit as st
import pandas as pd
import asyncio
from src.data_sources.macro_source import MacroSource
from src.data_sources.sector_source import SectorSource
from src.analyzer import StockAnalyzer
import plotly.graph_objects as go

def render_market_pulse_page():
    # Inject Custom 'Glassmorphism' CSS for Macro Cards
    st.markdown("""
        <style>
        .macro-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            text-align: center;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .macro-card:hover {
            transform: translateY(-5px);
            border-color: rgba(255, 255, 255, 0.3);
            background: rgba(255, 255, 255, 0.08);
        }
        .macro-label { color: #94a3b8; font-size: 0.85rem; font-weight: 500; margin-bottom: 8px; }
        .macro-value { font-size: 1.5rem; font-weight: 700; margin-bottom: 4px; }
        .macro-delta { font-size: 0.9rem; font-weight: 600; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🌍 Market Pulse")
    
    # Fetch Data
    with st.spinner("Fetching global market data..."):
        macro_data = MacroSource().fetch_macro_data()
    
    if not macro_data:
        st.error("Could not fetch market pulse data. Please check your internet connection.")
        return

    # --- TABBED INTERFACE ---
    tab_global, tab_sector = st.tabs(["🌎 Global Pulse", "🎯 Sector Watchlist"])

    with tab_global:
        # Row 1: Interest Rates (The "Economic Engine")
        st.subheader("🏦 Yields & Rates")
        cols = st.columns(4)
        yield_metrics = [
            ('10Y_Yield', 'US 10Y Yield', cols[0]),
            ('5Y_Yield', 'US 5Y Yield', cols[1]),
            ('Short_Yield', 'US 3M Yield', cols[2]),
            ('Yield_Spread', '10Y-3M Spread', cols[3])
        ]
        
        for key, label, col in yield_metrics:
            val = macro_data.get(key)
            if val:
                with col:
                    delta_str = f"{val.get('pct_change', 0):+.2f}%" if 'pct_change' in val else ""
                    delta_color = "normal" if val.get('value', 0) > 0 else "inverse"
                    if key == 'Yield_Spread':
                        delta_str = "Inversion Risk" if val['value'] < 0 else "Healthy"
                        delta_color = "inverse" if val['value'] < 0 else "normal"
                    
                    st.markdown(f"""
                        <div class="macro-card">
                            <div class="macro-label">{label}</div>
                            <div class="macro-value">{val['value']:.2f}%</div>
                            <div class="macro-delta" style="color: {'#ef4444' if delta_color == 'inverse' else '#10b981'}">{delta_str}</div>
                        </div>
                    """, unsafe_allow_html=True)

        # Row 2: Risk & Equity
        st.write("")
        st.subheader("📉 Risk & Equity Pulse")
        cols2 = st.columns(3)
        risk_metrics = [
            ('VIX', 'VIX (Fear Index)', cols2[0]),
            ('SPY', 'S&P 500 (SPY)', cols2[1]),
            ('Dollar_Index', 'US Dollar Index', cols2[2])
        ]
        
        for key, label, col in risk_metrics:
            val = macro_data.get(key)
            if val:
                with col:
                    prefix = "$" if key == 'SPY' else ""
                    suffix = ""
                    delta = f"{val['pct_change']:+.2f}%"
                    # VIX: Up is bad (Inverse color)
                    d_color = "inverse" if key == 'VIX' else "normal"
                    
                    st.markdown(f"""
                        <div class="macro-card">
                            <div class="macro-label">{label}</div>
                            <div class="macro-value">{prefix}{val['value']:.2f}{suffix}</div>
                            <div class="macro-delta" style="color: {'#ef4444' if (val['pct_change'] > 0 and d_color == 'inverse') or (val['pct_change'] < 0 and d_color == 'normal') else '#10b981'}">{delta}</div>
                        </div>
                    """, unsafe_allow_html=True)

        st.divider()
        st.subheader("📊 Sector Heatmap (1D)")
        with st.spinner("Calculating sector trends..."):
            sector_data = MacroSource().fetch_sector_data()
            
        if sector_data:
            df_sector = pd.DataFrame(list(sector_data.items()), columns=['Sector', 'Performance'])
            df_sector = df_sector.sort_values('Performance', ascending=True)
            colors = ['#ef4444' if x < 0 else '#10b981' for x in df_sector['Performance']]
            
            import plotly.graph_objects as go
            fig = go.Figure(go.Bar(
                x=df_sector['Performance'],
                y=df_sector['Sector'],
                orientation='h',
                marker_color=colors,
                text=[f"{x:+.2f}%" for x in df_sector['Performance']],
                textposition='auto',
            ))
            fig.update_layout(xaxis_title="Daily Change %", height=450, margin=dict(l=20, r=20, t=40, b=20),
                            template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("📈 Yield Trend (1 Year)")
        hist_10y = MacroSource().fetch_historical_macro('10Y_Yield')
        if isinstance(hist_10y, pd.DataFrame) and not hist_10y.empty:
            st.line_chart(hist_10y['Close'])

    with tab_sector:
        st.subheader("🎯 Sector Ticker Watchlist")
        st.markdown("Drill down into the Top 15 giants of each sector by Market Cap.")

        from src.data_sources.ticker_scraper import SectorTickerScraper
        scraper = SectorTickerScraper()
        
        # 1. Select Sector
        sector_list = list(SectorTickerScraper.SECTOR_MAPPING.keys())
        default_sector = sector_list[0]
        if sector_data:
            sorted_sectors = sorted(sector_data.items(), key=lambda x: x[1], reverse=True)
            if sorted_sectors:
                best_sector = sorted_sectors[0][0]
                if best_sector in sector_list:
                    default_sector = best_sector

        col_sel, col_btn = st.columns([0.4, 0.6])
        with col_sel:
            selected_sector = st.selectbox("Market Sector:", sector_list, index=sector_list.index(default_sector), key="mp_sector_sel")
        
        # 2. Fetch Leaders
        with st.spinner(f"Scanning {selected_sector} Leaders..."):
            buster = st.session_state.get(f'buster_{selected_sector}', 0)
            top_tickers = scraper.fetch_top_tickers(selected_sector, _cache_buster=buster)
            
        if top_tickers:
            is_fallback = any(t.get('is_fallback') for t in top_tickers)
            
            # Action Buttons
            with col_btn:
                st.write("") # Padding
                c_batch, c_audit, c_reload = st.columns([0.4, 0.4, 0.2])
                with c_batch:
                    batch_btn = st.button(f"🚀 Analyze {len(top_tickers)} Leaders", type="secondary", use_container_width=True, help="Run Multi-Style analysis on all")
                with c_audit:
                    audit_btn = st.button(f"🔍 Run 9-Point Quality Audit", type="primary", use_container_width=True, help="Screen fundamentals from Macrotrends/Finviz")
                with c_reload:
                    if st.button("🔄", key="mp_reload_btn", use_container_width=True):
                        import time
                        st.session_state[f'buster_{selected_sector}'] = time.time()
                        st.rerun()

            if is_fallback:
                st.info("🏛️ **S&P 500 Benchmark View**: Showing verified index giants.")
            
            # --- Audit Logic ---
            if audit_btn:
                with st.status(f"Scanning Fundamental Health for {len(top_tickers)} tickers...", expanded=True) as status:
                    st.write("📡 Connecting to Macrotrends & Finviz...")
                    analyzer = StockAnalyzer()
                    tickers_to_scan = [t['ticker'] for t in top_tickers]
                    
                    # Run async scan
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    audit_results = loop.run_until_complete(analyzer.scan_tickers_quality(tickers_to_scan))
                    
                    st.session_state[f'quality_audit_{selected_sector}'] = audit_results
                    status.update(label="✅ Quality Audit Complete!", state="complete", expanded=False)
                    st.rerun()

            if batch_btn:
                ticker_string = ",".join([t['ticker'] for t in top_tickers])
                st.session_state['ms_report_text'] = ticker_string
                st.session_state['go_to_page'] = '🏁 Multi-Style'
                st.toast("Redirecting to Multi-Style engine...", icon="🚀")
                st.rerun()

            # Map columns for cleaner display
            col_map = {
                'ticker': 'Ticker',
                'company': 'Company Name',
                'market_cap_str': 'Valuation',
                'price': 'Last Price',
                'change': '1D Change',
                'quality_score': 'Score (9/9)'
            }

            # Merge Audit results if available
            df_display = pd.DataFrame(top_tickers)
            df_display['market_cap_str'] = df_display['market_cap']
            
            audit_data = st.session_state.get(f'quality_audit_{selected_sector}')
            if audit_data:
                audit_df = pd.DataFrame(audit_data)
                
                # Verify required columns exist to prevent KeyError
                required_cols = {'ticker', 'score', 'market_cap'}
                if required_cols.issubset(audit_df.columns):
                    df_display = df_display.merge(audit_df[['ticker', 'score', 'market_cap']], on='ticker', suffixes=('', '_val'))
                    df_display['quality_score'] = df_display['score'].apply(lambda x: f"🌟 {x}/9" if x >= 8 else (f"✅ {x}/9" if x >= 6 else f"⚠️ {x}/9"))
                    
                    # Sorting by score then market_cap
                    df_display = df_display.sort_values(by=['score', 'market_cap_val'], ascending=[False, False])
                    
                    # Show Recommendation Card
                    top_q = df_display[df_display['score'] >= 8]
                    if not top_q.empty:
                        st.success(f"🏆 **Quality Recommendations**: {', '.join(top_q['ticker'].tolist())} passed {top_q['score'].max()}/9 points!")

                    display_cols = ['ticker', 'company', 'market_cap_str', 'quality_score']
                else:
                    st.warning("⚠️ Partial scan data received. Please try reloading the audit.")
                    display_cols = ['ticker', 'company', 'market_cap_str']
            else:
                # Standard view
                display_cols = ['ticker', 'company', 'market_cap_str']
                
            if not is_fallback:
                display_cols.append('price')
                display_cols.append('change')
            
            # Configure the table
            st.data_editor(
                df_display[display_cols].rename(columns=col_map),
                column_config={
                    "Ticker": st.column_config.TextColumn("Ticker", help="Stock Symbol", width="small"),
                    "Company Name": st.column_config.TextColumn("Company", width="large"),
                    "Valuation": st.column_config.TextColumn("Market Cap", help="Total Valuation"),
                    "Last Price": st.column_config.TextColumn("Price"),
                    "1D Change": st.column_config.TextColumn("Change %", help="Daily performance", width="small"),
                    "Score (9/9)": st.column_config.TextColumn("Quality Score", help="Fundamental Health Score out of 9")
                },
                use_container_width=True,
                hide_index=True,
                disabled=True, # Read-only but selectable
                key=f"mp_table_{selected_sector}_v2" # Changed key to avoid conflict after col change
            )
            
            # Quick Action for individual ticker
            st.write("")
            c_label, c_ticker, c_go = st.columns([0.2, 0.4, 0.4])
            with c_label:
                st.markdown("**Quick Analyze:**")
            with c_ticker:
                target_ticker = st.selectbox("Select ticker from list:", [t['ticker'] for t in top_tickers], label_visibility="collapsed")
            with c_go:
                if st.button(f"🔬 Deep-Dive {target_ticker}", type="secondary", use_container_width=True):
                    # Set navigation triggers
                    st.session_state['main_dash_text'] = target_ticker
                    st.session_state['go_to_page'] = '🏠 Home'
                    st.session_state['mp_deep_dive_trigger'] = True
                    st.rerun()

        else:
            st.warning(f"No results found for {selected_sector}. Try a manual reload.")

    st.caption("Data provided by Yahoo Finance & Wikipedia. Reference mode uses current S&P 500 constituents. Yields represent daily closing rates.")
