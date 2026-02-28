"""Portfolio Tracker page for managing real trades"""

import streamlit as st
import pandas as pd
import yfinance as yf
from src.database import Database
from src.portfolio_manager import PortfolioManager
from src.activity_logger import log_page_visit

def render_portfolio_tracker_page():
    st.title("💼 Portfolio Tracker")
    st.markdown("Track your actual stock positions and monitor performance vs the market.")
    # -- Activity tracking --
    _db = st.session_state.get('db')
    if _db:
        log_page_visit(_db, "Portfolio")
    
    # Get database instance
    try:
        from src.dashboard import init_database
        db = init_database()
        if 'db' not in st.session_state:
            st.session_state['db'] = db
    except ImportError:
        # Fallback if run standalone
        db = st.session_state.get('db')
        if not db:
            db = Database()
            db.init_db()
            st.session_state['db'] = db

    # Initialize Manager
    with db.get_session() as session:
        user_id = st.session_state.get('user_id', 1)
        pm = PortfolioManager(session, user_id)
        
        # 1. Manage Portfolios
        portfolios = db.get_all_portfolios(user_id)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if not portfolios:
                st.info("You haven't created any portfolios yet. Create your first one to start tracking!")
                portfolio_name = st.text_input("New Portfolio Name", placeholder="e.g. Long Term Growth")
                initial_nlv = st.number_input("Initial Deposit / Starting NLV ($)", min_value=1.0, value=10000.0, step=100.0)
                if st.button("Create Portfolio"):
                    # Enforce Free Tier Limits for portfolios
                    tier = st.session_state.get('user_tier', 'free')
                    if tier == 'free' and len(portfolios) >= 1: # If no portfolios, len(portfolios) is 0, so this check passes
                        st.error("Free tier is limited to 1 portfolio. Please upgrade to Premium to unlock unlimited portfolios.")
                        st.stop()
                    
                    pm.create_portfolio(portfolio_name, initial_balance=initial_nlv)
                    st.rerun()
            else:
                portfolio_ids = [p.id for p in portfolios]
                portfolio_formats = {p.id: p.name for p in portfolios}
                
                col_select, col_delete = st.columns([4, 1])
                with col_select:
                    selected_id = st.selectbox(
                        "Select Portfolio",
                        options=portfolio_ids,
                        format_func=lambda x: portfolio_formats.get(x, "Unknown"),
                        key="selected_portfolio_id"
                    )
                    from src.models import Portfolio
                    selected_portfolio = session.query(Portfolio).filter(Portfolio.id == selected_id).first()
                    
                with col_delete:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑️ Delete", help="Permanently delete this portfolio and all its transactions"):
                        if pm.delete_portfolio(selected_id):
                            st.success(f"Deleted")
                            st.rerun()
        
        with col2:
            if portfolios:
                if st.button("➕ Create New Portfolio"):
                    st.session_state['show_new_portfolio'] = True
                    
                if st.session_state.get('show_new_portfolio'):
                    with st.form("new_portfolio_form"):
                        new_name = st.text_input("Portfolio Name")
                        new_desc = st.text_area("Description")
                        initial_nlv = st.number_input("Initial Deposit / Starting NLV ($)", min_value=1.0, value=10000.0, step=100.0)
                        if st.form_submit_button("Save"):
                            pm.create_portfolio(new_name, new_desc, initial_balance=initial_nlv)
                            st.session_state['show_new_portfolio'] = False
                            st.rerun()

        if not portfolios:
            return

        # 2. Add Transactions
        st.divider()
        with st.expander("📝 Add New Transaction"):
            with st.form("transaction_form"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    ticker = st.text_input("Ticker", placeholder="AAPL").upper()
                with col2:
                    trans_type = st.selectbox("Type", ["BUY", "SELL"])
                with col3:
                    date = st.date_input("Date")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    qty = st.number_input("Quantity", min_value=0.01, step=0.01)
                with col2:
                    price = st.number_input("Price per Share", min_value=0.01, step=0.01)
                with col3:
                    fees = st.number_input("Commission/Fees", min_value=0.0, step=0.01)
                
                notes = st.text_area("Notes")
                if st.form_submit_button("Add Transaction"):
                    pm.add_transaction(selected_portfolio.id, ticker, trans_type, qty, price, fees, notes)
                    st.success(f"Added {trans_type} for {ticker}")
                    st.rerun()

        # 3. Quick Deletion / Management
        with st.expander("🛠️ Manage Positions"):
            tickers_to_manage = [t.stock.ticker for t in selected_portfolio.transactions]
            unique_tickers = sorted(list(set(tickers_to_manage)))
            if not unique_tickers:
                st.info("No active positions to manage.")
            else:
                del_ticker = st.selectbox("Select Position to Remove", options=unique_tickers)
                if st.button(f"🗑️ Delete All {del_ticker} Transactions", use_container_width=True):
                    if pm.delete_ticker_from_portfolio(selected_portfolio.id, del_ticker):
                        st.success(f"Removed all records for {del_ticker}")
                        st.rerun()

        # Premium Position Sizing Calculator
        import math
        from src.utils_tickers import render_hybrid_ticker_input
        from src.analyzer import StockAnalyzer
        import asyncio
        
        st.divider()
        tier = st.session_state.get('user_tier', 'free')
        is_premium = tier in ['premium', 'admin']
        
        with st.expander("🛡️ Risk & Position Sizing Calculator (Premium)"):
            if not is_premium:
                st.warning("👑 This is a Premium feature. Upgrade your account to unlock advanced risk management & portfolio sizing.")
            else:
                st.markdown("Calculate exactly how many shares to buy to keep your risk under 1% of your NLV.")
                colA, colB = st.columns(2)
                with colA:
                    sizer_ticker = render_hybrid_ticker_input(key_prefix="sizer")
                
                with colB:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Fetch Advanced Analytics Data"):
                        with st.spinner("Fetching data..."):
                            analyzer = StockAnalyzer()
                            analysis = asyncio.run(analyzer.analyze(sizer_ticker))
                            if analysis:
                                st.session_state[f'sizer_analysis_{sizer_ticker}'] = analysis # Cache full analysis
                                st.session_state[f'sizer_entry_{sizer_ticker}'] = analysis.suggested_entry
                                st.session_state[f'sizer_stop_{sizer_ticker}'] = analysis.suggested_stop_loss
                                st.success("AI Intelligence Data Loaded!")
                            else:
                                st.error("Failed to fetch analysis.")
                
                s_col1, s_col2 = st.columns(2)
                with s_col1:
                    default_entry = st.session_state.get(f'sizer_entry_{sizer_ticker}', 0.0)
                    planned_entry = st.number_input("Planned Entry Price", min_value=0.01, value=float(default_entry) if default_entry else 100.0, step=0.1)
                with s_col2:
                    default_stop = st.session_state.get(f'sizer_stop_{sizer_ticker}', 0.0)
                    planned_stop = st.number_input("Planned Stop Loss", min_value=0.01, value=float(default_stop) if default_stop else 90.0, step=0.1)

                # --- NEW COMPREHENSIVE AI REPORT SECTION ---
                analysis = st.session_state.get(f'sizer_analysis_{sizer_ticker}')
                if analysis:
                    st.markdown("---")
                    st.subheader(f"🤖 AI Intelligence Report: {sizer_ticker}")
                    
                    # Row 1: The Pulse
                    col1, col2, col3, col4 = st.columns(4)
                    trend = getattr(analysis, 'market_trend', 'Sideways')
                    col1.metric("Trend", trend)
                    
                    rsi = getattr(analysis, 'rsi', 50.0)
                    rsi_status = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
                    col2.metric("RSI (14)", f"{rsi:.1f}", delta=rsi_status, delta_color="inverse" if rsi > 70 else "normal")
                    
                    target = getattr(analysis, 'median_price_target', 0.0)
                    if target:
                        upside = ((target / analysis.current_price) - 1) * 100
                        col3.metric("Analyst Target", f"${target:,.2f}", f"{upside:+.1f}% upside")
                    else:
                        col3.metric("Analyst Target", "N/A")
                        
                    sent = getattr(analysis, 'news_sentiment', 0.0) or 0.0
                    col4.metric("Sentiment", f"{sent:+.2f}", "Bullish" if sent > 0.1 else "Bearish" if sent < -0.1 else "Neutral")

                    # Row 2: Deep Dive Tabs
                    tab1, tab2, tab3, tab4 = st.tabs(["📊 Technicals", "📈 Fundamentals", "🎯 Targets & Levels", "📰 News & Insider"])
                    
                    with tab1:
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("**Moving Averages**")
                            st.write(f"- EMA 20: ${getattr(analysis, 'ema20', 0):.2f}")
                            st.write(f"- EMA 50: ${getattr(analysis, 'ema50', 0):.2f}")
                            st.write(f"- EMA 200: ${getattr(analysis, 'ema200', 0):.2f}")
                        with c2:
                            st.markdown("**Volatility & Range**")
                            st.write(f"- ATR (14): ${getattr(analysis, 'atr', 0):.2f}")
                            bb_upper = getattr(analysis, 'bollinger_upper', 0)
                            bb_lower = getattr(analysis, 'bollinger_lower', 0)
                            st.write(f"- Bollinger Upper: ${bb_upper:.2f}")
                            st.write(f"- Bollinger Lower: ${bb_lower:.2f}")

                    with tab2:
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("**Valuation**")
                            st.write(f"- P/E Ratio: {analysis.finviz_data.get('P/E', 'N/A')}")
                            st.write(f"- Forward P/E: {analysis.finviz_data.get('Forward P/E', 'N/A')}")
                            st.write(f"- PEG: {analysis.finviz_data.get('PEG', 'N/A')}")
                        with c2:
                            st.markdown("**Growth (YoY)**")
                            rev_growth = getattr(analysis, 'revenue_growth_yoy', 0)
                            eps_growth = getattr(analysis, 'eps_growth_yoy', 0)
                            st.write(f"- Revenue Growth: {rev_growth*100:.1f}%" if rev_growth else "- Revenue Growth: N/A")
                            st.write(f"- EPS Growth: {eps_growth*100:.1f}%" if eps_growth else "- EPS Growth: N/A")

                    with tab3:
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("**Support & Entry**")
                            st.write(f"👉 **Suggested Entry: ${getattr(analysis, 'suggested_entry', 0):.2f}**")
                            st.write(f"🛑 **Suggested Stop: ${getattr(analysis, 'suggested_stop_loss', 0):.2f}**")
                            st.divider()
                            for s in sorted(analysis.support_levels, reverse=True):
                                st.write(f"🟢 Support: ${s:.2f}")
                        with c2:
                            st.markdown("**Resistance Levels**")
                            for r in sorted(analysis.resistance_levels):
                                st.write(f"🔴 Resistance: ${r:.2f}")

                    with tab4:
                        st.markdown("**AI News Analysis**")
                        st.info(analysis.news_summary if analysis.news_summary else "No recent news summary available.")
                        insider = getattr(analysis, 'insider_ownership_pct', 0)
                        if insider:
                            st.write(f"**Insider Ownership:** {insider:.2f}%")
                    
                    st.markdown("---")

                if planned_entry > planned_stop:
                    risk_per_share = planned_entry - planned_stop
                    
                    # Calculate NLV dynamically if possible, or fallback to the manager 
                    # Wait, we need the performance dict for NLV. Let's fetch it here.
                    with st.spinner("Calculating NLV..."):
                        current_prices = {}
                        holdings_for_nlv = pm.get_portfolio_holdings(selected_portfolio.id)
                        if not holdings_for_nlv.empty:
                            for idx, row in holdings_for_nlv.iterrows():
                                try:
                                    t = yf.Ticker(row['Ticker'])
                                    current_prices[row['Ticker']] = getattr(t, 'fast_info', {}).get('lastPrice', 0.0)
                                except:
                                    current_prices[row['Ticker']] = 0.0
                                
                        perf = pm.get_portfolio_performance(selected_portfolio.id, current_prices)
                        current_nlv = perf.get('nlv', selected_portfolio.initial_balance)
                        
                        # 1. Risk-Based sizing (1% of NLV)
                        allowed_risk_dollars = current_nlv * 0.01 
                        shares_by_risk = math.floor(allowed_risk_dollars / risk_per_share) if risk_per_share > 0 else 0
                        
                        # 2. Capital-Based sizing (5% of NLV)
                        max_capital_dollars = current_nlv * 0.05
                        shares_by_capital = math.floor(max_capital_dollars / planned_entry) if planned_entry > 0 else 0
                        
                        # Take the safer of the two
                        suggested_shares = min(shares_by_risk, shares_by_capital)
                        total_capital_required = suggested_shares * planned_entry
                        
                        # Calculation Logic Explanation
                        st.info(f"**Portfolio Risk Analysis**")
                        st.markdown(f"""
                        - **Current NLV:** ${current_nlv:,.2f}
                        - **1% Risk Budget:** ${allowed_risk_dollars:,.2f} (Max loss if stop hit)
                        - **5% Capital Cap:** ${max_capital_dollars:,.2f} (Max position size)
                        """)
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Risk Per Share", f"${risk_per_share:.2f}")
                        m2.metric("Recommended Shares", f"{suggested_shares}")
                        m3.metric("Total Capital", f"${total_capital_required:,.2f}")
                        
                        if shares_by_capital < shares_by_risk:
                            st.warning(f"⚠️ **Sizing constrained by Capital Rule**: Your 1% risk rule allows {shares_by_risk} shares, but you are capped at {shares_by_capital} shares to keep position size under 5% of NLV.")
                        
                        if total_capital_required > perf.get('cash_balance', 0):
                            st.error(f"⚠️ **Insufficient Funds**: You need ${total_capital_required:,.2f} but only have ${perf.get('cash_balance', 0):,.2f} cash available.")
                            
                        # Sector Concentration Check
                        sector_alloc = perf.get('sector_allocation', {})
                        if stock_obj := db.get_or_create_stock(session, sizer_ticker):
                            target_sector = stock_obj.sector
                            if target_sector and target_sector in sector_alloc:
                                current_exposure = sector_alloc[target_sector]
                                if current_exposure > 25.0: # Arbitrary warning threshold
                                    st.warning(f"⚠️ Sector Warning: You already have {current_exposure:.1f}% of your portfolio exposed to {target_sector}.")
                else:
                    st.error("Stop Loss must be below Entry Price for a long position.")

        # 3. View Holdings
        st.subheader(f"📊 {selected_portfolio.name} Holdings")
        holdings_df = pm.get_portfolio_holdings(selected_portfolio.id)
        
        if holdings_df.empty:
            st.info("No active holdings in this portfolio.")
            return

        # Fetch current prices for performance
        with st.spinner("Fetching real-time prices..."):
            current_prices = {}
            for ticker in holdings_df['Ticker']:
                if ticker == '💰 CASH' or ticker == '🏦 TOTAL NLV': continue
                try:
                    t = yf.Ticker(ticker)
                    current_prices[ticker] = getattr(t, 'fast_info', {}).get('lastPrice', 0.0)
                except:
                    current_prices[ticker] = 0.0

        performance = pm.get_portfolio_performance(selected_portfolio.id, current_prices)
        
        # Summary Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Net Liquidation Value", f"${performance.get('nlv', 0):,.2f}")
        m2.metric("Available Cash", f"${performance.get('cash_balance', 0):,.2f}")
        m3.metric("Total Invested", f"${performance.get('total_value', 0):,.2f}")
        m4.metric("Total P/L", f"${performance.get('total_pl', 0):,.2f}", f"{performance.get('total_pl_pct', 0):.2f}%")
        
        # Detailed Table
        st.divider()
        holdings_display = holdings_df.copy()
        holdings_display['Current Price'] = holdings_display['Ticker'].map(current_prices)
        holdings_display['Current Value'] = holdings_display['qty'] * holdings_display['Current Price']
        holdings_display['P/L $'] = holdings_display['Current Value'] - holdings_display['total_spent']
        holdings_display['P/L %'] = (holdings_display['P/L $'] / holdings_display['total_spent']) * 100
        
        # Reorder and filter columns
        col_order = ['Ticker', 'Entry Date', 'qty', 'cost_basis', 'Current Price', 'Current Value', 'P/L $', 'P/L %']
        holdings_display = holdings_display[col_order]
        
        # Add Cash and NLV Rows
        cash_balance = performance.get('cash_balance', 0)
        nlv = performance.get('nlv', 0)
        
        summary_rows = pd.DataFrame([
            {
                'Ticker': '💰 CASH',
                'Entry Date': None,
                'qty': 1.0,
                'cost_basis': cash_balance,
                'Current Price': cash_balance,
                'Current Value': cash_balance,
                'P/L $': 0.0,
                'P/L %': 0.0
            },
            {
                'Ticker': '🏦 TOTAL NLV',
                'Entry Date': None,
                'qty': 1.0,
                'cost_basis': nlv,
                'Current Price': nlv,
                'Current Value': nlv,
                'P/L $': performance.get('total_pl', 0),
                'P/L %': performance.get('total_pl_pct', 0)
            }
        ])
        holdings_display = pd.concat([holdings_display, summary_rows], ignore_index=True)

        # Formatting
        st.dataframe(
            holdings_display.style.format({
                'qty': '{:.2f}',
                'cost_basis': '${:.2f}',
                'Current Price': '${:.2f}',
                'Current Value': '${:.2f}',
                'P/L $': '{:+.2f}',
                'P/L %': '{:+.2f}%',
                'Entry Date': lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else ""
            }),
            use_container_width=True,
            hide_index=True
        )
