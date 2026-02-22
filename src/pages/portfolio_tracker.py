"""Portfolio Tracker page for managing real trades"""

import streamlit as st
import pandas as pd
import yfinance as yf
from src.database import Database
from src.portfolio_manager import PortfolioManager

def render_portfolio_tracker_page():
    st.title("💼 Portfolio Tracker")
    st.markdown("Track your actual stock positions and monitor performance vs the market.")
    
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
                selected_portfolio = st.selectbox(
                    "Select Portfolio",
                    options=portfolios,
                    format_func=lambda x: x.name
                )
        
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
                                st.session_state[f'sizer_entry_{sizer_ticker}'] = analysis.suggested_entry
                                st.session_state[f'sizer_stop_{sizer_ticker}'] = analysis.suggested_stop_loss
                                st.success("Auto-filled from technical support levels!")
                            else:
                                st.error("Failed to fetch analysis.")
                
                s_col1, s_col2 = st.columns(2)
                with s_col1:
                    default_entry = st.session_state.get(f'sizer_entry_{sizer_ticker}', 0.0)
                    planned_entry = st.number_input("Planned Entry Price", min_value=0.01, value=float(default_entry) if default_entry else 100.0, step=0.1)
                with s_col2:
                    default_stop = st.session_state.get(f'sizer_stop_{sizer_ticker}', 0.0)
                    planned_stop = st.number_input("Planned Stop Loss", min_value=0.01, value=float(default_stop) if default_stop else 90.0, step=0.1)

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
                                    current_prices[row['Ticker']] = t.fast_info['lastPrice']
                                except:
                                    current_prices[row['Ticker']] = 0.0
                                
                        perf = pm.get_portfolio_performance(selected_portfolio.id, current_prices)
                        current_nlv = perf.get('nlv', selected_portfolio.initial_balance)
                        
                        allowed_risk = current_nlv * 0.01 # 1% account risk
                        suggested_shares_by_risk = math.floor(allowed_risk / risk_per_share) if risk_per_share > 0 else 0
                        
                        # Cap position size at 5% of total NLV
                        max_capital_allowed = current_nlv * 0.05
                        suggested_shares_by_cap = math.floor(max_capital_allowed / planned_entry) if planned_entry > 0 else 0
                        
                        # Take the safer (smaller) of the two constraints
                        suggested_shares = min(suggested_shares_by_risk, suggested_shares_by_cap)
                        total_capital_required = suggested_shares * planned_entry
                        
                        st.info(f"**Current NLV:** ${current_nlv:,.2f} | **1% Max Risk:** ${allowed_risk:,.2f} | **5% Max Capital:** ${max_capital_allowed:,.2f}")
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Risk Per Share", f"${risk_per_share:.2f}")
                        m2.metric("Recommended Shares", f"{suggested_shares}")
                        m3.metric("Capital Required", f"${total_capital_required:,.2f}")
                        
                        if suggested_shares_by_risk > suggested_shares_by_cap:
                            st.warning(f"⚠️ Sizing artificially constrained. Although 1% risk allows {suggested_shares_by_risk} shares, the 5% maximum portfolio capital rule caps you at {suggested_shares_by_cap} shares.")
                            
                        if total_capital_required > perf.get('cash_balance', 0):
                            st.warning(f"⚠️ Warning: This trade requires ${total_capital_required:,.2f}, but you only have ${perf.get('cash_balance', 0):,.2f} in Available Cash.")
                            
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
                try:
                    t = yf.Ticker(ticker)
                    current_prices[ticker] = t.fast_info['lastPrice']
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
        
        # Formatting
        st.dataframe(
            holdings_display.style.format({
                'qty': '{:.2f}',
                'cost_basis': '${:.2f}',
                'total_spent': '${:.2f}',
                'Current Price': '${:.2f}',
                'Current Value': '${:.2f}',
                'P/L $': '{:+.2f}',
                'P/L %': '{:+.2f}%'
            }),
            use_container_width=True
        )
