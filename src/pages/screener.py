"""Automated stock screener page for Streamlit dashboard"""

import streamlit as st
import pandas as pd
import asyncio
from src.analyzer import StockAnalyzer
from src.screener_engine import ScreenerEngine
from src.utils import render_ticker_header
from src.database import Database

# Some common universes for quick testing
UNIVERSES = {
    "Custom List": [],
    "Mega-Cap Tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"],
    "Dow Jones 30": [
        "MMM", "AXP", "AMGN", "AAPL", "BA", "CAT", "CVX", "CSCO", "KO", "DOW", 
        "GS", "HD", "HON", "IBM", "INTC", "JNJ", "JPM", "MCD", "MRK", "MSFT", 
        "NKE", "PG", "CRM", "TRV", "UNH", "VZ", "V", "WMT", "DIS"
    ]
}

def render_screener_page():
    """Render the automated screener page"""
    st.title("🔍 Automated Screener")
    st.markdown("Scan multiple stocks simultaneously against the Growth Investment Checklist criteria.")
    
    # Initialize DB safely for standalone reloads
    try:
        from src.dashboard import init_database
        db = init_database()
        if 'db' not in st.session_state:
            st.session_state['db'] = db
    except ImportError:
        db = st.session_state.get('db')
        if not db:
            db = Database()
            db.init_db()
            st.session_state['db'] = db

    # Universe Selection
    col1, col2 = st.columns([2, 2])
    
    with col1:
        selected_universe = st.selectbox(
            "Select Stock Universe",
            options=list(UNIVERSES.keys())
        )
    
    custom_tickers = ""
    with col2:
        if selected_universe == "Custom List":
            custom_tickers = st.text_input("Enter Tickers (comma separated)", value="AAPL, NVDA, AMD, INTC")
            
    # Compile final list to scan
    tickers_to_scan = []
    if selected_universe == "Custom List" and custom_tickers.strip():
        tickers_to_scan = [t.strip().upper() for t in custom_tickers.split(",") if t.strip()]
    elif selected_universe != "Custom List":
        tickers_to_scan = UNIVERSES[selected_universe]
        
    st.markdown(f"**Total Stocks to Scan:** {len(tickers_to_scan)}")
    
    # Run Screener
    if st.button("🚀 Run Screener", type="primary") and tickers_to_scan:
        st.divider()
        st.subheader("Screener Results")
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        analyzer = StockAnalyzer()
        results_data = []
        
        async def scan_tickers():
            total = len(tickers_to_scan)
            for i, ticker in enumerate(tickers_to_scan):
                status_text.text(f"Analyzing {ticker} ({i+1}/{total})...")
                
                try:
                    # Run full analysis
                    analysis = await analyzer.analyze(ticker, verbose=False)
                    if analysis:
                        # Evaluate against screener
                        is_passing, score, max_score, reasons = ScreenerEngine.evaluate(analysis)
                        
                        results_data.append({
                            "Ticker": ticker,
                            "Company": getattr(analysis, 'company_name', ticker),
                            "Price": f"${analysis.current_price:.2f}" if analysis.current_price else "N/A",
                            "Score": f"{score}/{max_score}",
                            "Passes?": "✅ YES" if is_passing else "❌ NO",
                            "Failing Reasons": ", ".join(reasons) if reasons else "None",
                            "Setup Notes": " | ".join(analysis.setup_notes) if hasattr(analysis, 'setup_notes') else ""
                        })
                except Exception as e:
                    st.error(f"Error processing {ticker}: {e}")
                
                # Update progress
                progress = (i + 1) / total
                progress_bar.progress(progress)
                
            status_text.text("Scan complete!")
            
        # Run async loop
        asyncio.run(scan_tickers())
        
        # Display Results
        if results_data:
            df = pd.DataFrame(results_data)
            
            # Sort so passing stocks are at the top
            df['is_pass_sort'] = df['Passes?'].str.contains('YES')
            df = df.sort_values(by=['is_pass_sort', 'Score'], ascending=[False, False])
            df = df.drop(columns=['is_pass_sort'])
            
            st.dataframe(df, use_container_width=True)
            
            # Display detailed setup notes for winners
            passing_df = df[df['Passes?'] == "✅ YES"]
            if not passing_df.empty:
                st.success(f"Found {len(passing_df)} stocks that passed the screener!")
                st.markdown("### Highlighted Trade Setups")
                for _, row in passing_df.iterrows():
                    with st.expander(f"⭐ {row['Ticker']} - {row['Company']}"):
                        st.markdown(f"**Current Price:** {row['Price']} | **Checklist Score:** {row['Score']}")
                        notes = row['Setup Notes'].split(' | ')
                        for note in notes:
                            if "✅" in note:
                                st.success(note)
                            elif "⚠️" in note:
                                st.warning(note)
                            elif "❌" in note:
                                st.error(note)
                            elif note:
                                st.info(note)
            else:
                st.warning("No stocks passed the strict Growth Checklist + Risk/Reward filters today.")
                
        else:
            st.error("No data could be retrieved for the selected tickers.")


if __name__ == "__main__":
    render_screener_page()
