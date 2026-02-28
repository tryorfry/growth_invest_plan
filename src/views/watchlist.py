"""Watchlist page for Streamlit dashboard"""

import streamlit as st
import pandas as pd
from src.database import Database
from src.watchlist import WatchlistManager
from src.analyzer import StockAnalyzer
from src.utils import save_analysis
import asyncio


def render_watchlist_page():
    """Render the watchlist management page"""
    st.title("📋 Watchlist Management")
    
    # Initialize
    db = st.session_state.get('db')
    if not db:
        db = Database()
        db.init_db()  # <-- CRITICAL: Ensures tables exist if page is loaded directly
        st.session_state['db'] = db
    
    session = db.SessionLocal()
    try:
        user_id = st.session_state.get('user_id', 1)
        wm = WatchlistManager(session, user_id)
        
        # Sidebar for watchlist selection
        with st.sidebar:
            st.header("Watchlists")
            
            # Get all watchlists
            watchlists = wm.get_all_watchlists()
            
            if watchlists:
                watchlist_names = {w.name: w.id for w in watchlists}
                selected_name = st.selectbox(
                    "Select Watchlist",
                    options=list(watchlist_names.keys())
                )
                selected_id = watchlist_names[selected_name]
            else:
                st.info("No watchlists yet. Create one below!")
                selected_id = None
            
            # Create new watchlist
            with st.expander("➕ Create New Watchlist"):
                new_name = st.text_input("Watchlist Name")
                new_desc = st.text_area("Description")
                if st.button("Create"):
                    if new_name:
                        wm.create_watchlist(new_name, new_desc)
                        st.success(f"Created watchlist: {new_name}")
                        st.rerun()
                    else:
                        st.error("Please enter a name")
        
        # Main content
        if selected_id:
            watchlist = wm.get_watchlist(selected_id)
            
            # Watchlist header
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"📊 {watchlist.name}")
                if watchlist.description:
                    st.caption(watchlist.description)
            
            with col2:
                if st.button("🗑️ Delete Watchlist", type="secondary"):
                    wm.delete_watchlist(selected_id)
                    st.success("Watchlist deleted")
                    st.rerun()
            
            # Add stock section
            with st.expander("➕ Add Stock to Watchlist"):
                from src.utils_tickers import render_hybrid_ticker_input
                
                new_ticker = render_hybrid_ticker_input(key_prefix=f"add_wl_{selected_id}")
                new_notes = st.text_input("Notes (optional)", key=f"notes_wl_{selected_id}")
                
                if st.button("Add Stock"):
                    if new_ticker:
                        item = wm.add_stock_to_watchlist(selected_id, new_ticker, new_notes)
                        if item:
                            st.success(f"Added {new_ticker} to watchlist")
                            st.rerun()
                    else:
                        st.error("Please select or enter a ticker")
            
            # Display stocks in watchlist
            stocks = wm.get_watchlist_stocks(selected_id)
            
            if stocks:
                st.markdown("---")
                st.subheader(f"Stocks ({len(stocks)})")
                
                # Create dataframe
                df_data = []
                for stock in stocks:
                    df_data.append({
                        'Ticker': stock['ticker'],
                        'Name': stock['name'] or 'N/A',
                        'Sector': stock['sector'] or 'N/A',
                        'Notes': stock['notes'] or '',
                        'Added': stock['added_at'].strftime('%Y-%m-%d') if stock['added_at'] else 'N/A'
                    })
                
                df = pd.DataFrame(df_data)
                
                # Display with actions
                for idx, row in df.iterrows():
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 3, 1])
                        
                        with col1:
                            st.markdown(f"**{row['Ticker']}**")
                        with col2:
                            st.text(row['Name'])
                        with col3:
                            st.text(row['Sector'])
                        with col4:
                            st.caption(row['Notes'])
                        
                        # Links and Actions
                        with col5:
                            yfin_url = f"https://finance.yahoo.com/quote/{row['Ticker']}"
                            finviz_url = f"https://finviz.com/quote.ashx?t={row['Ticker']}"
                            st.markdown(f"[YF]({yfin_url})|[FV]({finviz_url})")
                            
                            if st.button("🗑️", key=f"del_{row['Ticker']}"):
                                wm.remove_stock_from_watchlist(selected_id, row['Ticker'])
                                st.success(f"Removed {row['Ticker']}")
                                st.rerun()
                        
                        st.markdown("---")
                
                # Analyze all button
                if st.button("📊 Analyze All Stocks", type="primary"):
                    analyzer = StockAnalyzer()
                    
                    for stock in stocks:
                        ticker = stock['ticker']
                        
                        # Create a clean placeholder for the "Analyzing..." message
                        status_placeholder = st.empty()
                        
                        try:
                            with status_placeholder.container():
                                with st.spinner(f"Analyzing {ticker}..."):
                                    analysis = asyncio.run(analyzer.analyze(ticker))
                            
                            # Clear the spinner placeholder immediately after analysis is done
                            status_placeholder.empty()
                            
                            st.markdown(f"### **Analysis for {ticker}**")
                            
                            if analysis:
                                # Save to database
                                save_analysis(db, analysis)
                                
                                col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
                                with col1:
                                    st.metric("Price", f"${analysis.current_price:.2f}")
                                with col2:
                                    st.metric("RSI", f"{analysis.rsi:.1f}" if analysis.rsi else "N/A")
                                with col3:
                                    st.metric("P/E", analysis.finviz_data.get('P/E', 'N/A'))
                                with col4:
                                    st.metric("Market Cap", analysis.finviz_data.get('Market Cap', 'N/A'))
                                with col5:
                                    yfin_url = f"https://finance.yahoo.com/quote/{ticker}"
                                    finviz_url = f"https://finviz.com/quote.ashx?t={ticker}"
                                    st.markdown(f"**Links:**\n[YFinance]({yfin_url})\n[Finviz]({finviz_url})")
                            else:
                                st.error(f"Analysis failed for {ticker}. The ticker might be invalid or delisted.")
                                
                        except Exception as e:
                            status_placeholder.empty()
                            st.markdown(f"### **Analysis for {ticker}**")
                            st.error(f"⚠️ Error analyzing {ticker}: {e}")
                            
            else:
                st.info("No stocks in this watchlist yet. Add some above!")
        else:
            st.info("Create a watchlist to get started!")
    finally:
        session.close()


if __name__ == "__main__":
    render_watchlist_page()
