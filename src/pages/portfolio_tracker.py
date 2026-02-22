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
                if st.button("Create Portfolio"):
                    # Enforce Free Tier Limits for portfolios
                    tier = st.session_state.get('user_tier', 'free')
                    if tier == 'free' and len(portfolios) >= 1: # If no portfolios, len(portfolios) is 0, so this check passes
                        st.error("Free tier is limited to 1 portfolio. Please upgrade to Premium to unlock unlimited portfolios.")
                        st.stop()
                    
                    pm.create_portfolio(portfolio_name)
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
                        if st.form_submit_button("Save"):
                            pm.create_portfolio(new_name, new_desc)
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
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Value", f"${performance['total_value']:,.2f}")
        col2.metric("Total Cost", f"${performance['total_cost']:,.2f}")
        col3.metric("Total P/L", f"${performance['total_pl']:,.2f}", f"{performance['total_pl_pct']:.2f}%")
        
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
