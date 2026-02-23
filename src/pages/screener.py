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

    # Custom button color — override Streamlit's default primary (red) with a cool teal
    st.markdown("""
        <style>
        /* Analyze buttons in screener results — use Streamlit's actual data-testid attribute */
        button[data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, #0891b2, #0e7490) !important;
            border: none !important;
            color: white !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px;
            transition: background 0.2s ease, transform 0.1s ease;
        }
        button[data-testid="baseButton-primary"]:hover {
            background: linear-gradient(135deg, #06b6d4, #0891b2) !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(8, 145, 178, 0.4) !important;
        }
        button[data-testid="baseButton-primary"]:active {
            transform: translateY(0px);
        }
        </style>
    """, unsafe_allow_html=True)

    
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
            return results_data
            
        # Run async loop
        results = asyncio.run(scan_tickers())
        st.session_state['screener_results'] = results
        st.rerun() # Rerun to show results outside the button block
        
    # Display Results (Persistent)
    if 'screener_results' in st.session_state:
        results_data = st.session_state['screener_results']
        df = pd.DataFrame(results_data)
        
        # Sort so passing stocks are at the top
        df['is_pass_sort'] = df['Passes?'].str.contains('YES')
        df = df.sort_values(by=['is_pass_sort', 'Score'], ascending=[False, False])
        df = df.drop(columns=['is_pass_sort'])
        
        # --- NEW INTERACTIVE RESULTS TABLE ---
        st.markdown("### 📊 Scan Results")
        
        # Header
        h_cols = st.columns([1, 2, 1, 1, 1, 3, 2])
        h_cols[0].markdown("**Ticker**")
        h_cols[1].markdown("**Company**")
        h_cols[2].markdown("**Price**")
        h_cols[3].markdown("**Score**")
        h_cols[4].markdown("**Pass?**")
        h_cols[5].markdown("**Top Reasons**")
        h_cols[6].markdown("**Action**")
        st.divider()

        for _, row in df.iterrows():
            r_cols = st.columns([1, 2, 1, 1, 1, 3, 2])
            ticker = row['Ticker']
            r_cols[0].markdown(f"**{ticker}**")
            r_cols[1].markdown(row['Company'])
            r_cols[2].markdown(row['Price'])
            r_cols[3].markdown(row['Score'])
            r_cols[4].markdown(row['Passes?'])
            r_cols[5].write(row['Failing Reasons'][:50] + "..." if len(row['Failing Reasons']) > 50 else row['Failing Reasons'])
            
            if r_cols[6].button(f"🔬 Analyze {ticker}", key=f"btn_{ticker}", type="primary", use_container_width=True):
                st.session_state['screener_ticker'] = ticker
                st.session_state['go_to_page'] = "🔬 Advanced Analytics"
                st.session_state['run_adv_anal'] = True
                st.rerun()

        # Display detailed setup notes for winners
        passing_df = df[df['Passes?'] == "✅ YES"]
        if not passing_df.empty:
            st.divider()
            st.success(f"Found {len(passing_df)} stocks that passed the screener!")
            st.markdown("### Highlighted Trade Setups")
            for _, row in passing_df.iterrows():
                with st.expander(f"⭐ {row['Ticker']} - {row['Company']}"):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
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
                    with col_b:
                        if st.button(f"🔬 Full Analytics", key=f"exp_btn_{row['Ticker']}", type="primary", use_container_width=True):
                            st.session_state['screener_ticker'] = row['Ticker']
                            st.session_state['go_to_page'] = "🔬 Advanced Analytics"
                            st.session_state['run_adv_anal'] = True
                            st.rerun()
            
            if st.button("🗑️ Clear Results"):
                del st.session_state['screener_results']
                st.rerun()
        else:
            st.warning("No stocks passed the strict Growth Checklist + Risk/Reward filters today.")
            if st.button("🗑️ Clear Results"):
                del st.session_state['screener_results']
                st.rerun()


if __name__ == "__main__":
    render_screener_page()
