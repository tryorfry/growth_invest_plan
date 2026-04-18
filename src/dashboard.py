"""
Modular Streamlit Dashboard for Stock Analysis
"""

import streamlit as st
import asyncio
import sys
import os
from datetime import datetime

# Add root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st

# Page configuration - MUST BE FIRST
st.set_page_config(
    page_title="Growth Investment Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.analyzer import StockAnalyzer
from src.database import Database
from src.visualization_tv import TVChartGenerator
from src.auth import AuthManager
from src.theme_manager import ThemeManager
from src.views.sidebar import render_sidebar
from src.views.home import render_home_page
from src.views.login import render_login_page

# --- Resource Initialization ---

@st.cache_resource
def init_database():
    db = Database("stock_analysis.db")
    db.init_db()
    with db.get_session() as session:
        AuthManager.seed_admin(session)
    return db

@st.cache_resource
def init_analyzer():
    return StockAnalyzer()

@st.cache_resource
def init_chart_generator():
    return TVChartGenerator()

@st.cache_resource
def init_scheduler():
    from src.scheduler import start_scheduler_thread
    start_scheduler_thread()
    return True

# --- Main Application Router ---

def main():
    # 1. Initialize Backend
    db = init_database()
    analyzer = init_analyzer()
    chart_gen = init_chart_generator()
    init_scheduler()
    
    # 2. Session & Auth
    AuthManager.init_session_state()
    if 'db' not in st.session_state:
        st.session_state['db'] = db
        
    if 'chart_prefs' not in st.session_state:
        st.session_state['chart_prefs'] = {
            'ema': True, 'atr': True, 'sr': True, 'ts': True, 'rsi': False, 'macd': False, 'boll': False
        }

    if not AuthManager.is_authenticated():
        render_login_page()
        return
        
    ThemeManager.apply_theme()
    ThemeManager.inject_custom_css()
    
    # 3. Render Sidebar & Get Navigation Context
    page, ticker, analyze_button, selected_style = render_sidebar(db)
    
    # 4. View Routing
    if page == "🏠 Home":
        render_home_page(db, analyzer, chart_gen, ticker, selected_style, analyze_button)
        
    elif page == "💼 Portfolio":
        from src.views.portfolio_tracker import render_portfolio_tracker_page
        render_portfolio_tracker_page()
        
    elif page == "📋 Watchlist":
        from src.views.watchlist import render_watchlist_page
        render_watchlist_page()
        
    elif page == "🧪 Backtester":
        from src.views.backtest import render_backtesting_page
        render_backtesting_page()
        
    elif page == "🌍 Market Pulse":
        from src.views.market_pulse import render_market_pulse_page
        render_market_pulse_page()
        
    elif page == "🔍 Screener":
        from src.views.screener import render_screener_page
        render_screener_page()
        
    elif page == "🌊 Options Flow":
        from src.views.options_flow import render_options_flow_page
        render_options_flow_page()
        
    elif page == "🔔 Alerts":
        from src.views.alerts import render_alerts_page
        render_alerts_page()
        
    elif page == "🔬 Advanced Analytics":
        from src.views.advanced_analytics import render_advanced_analytics_page
        render_advanced_analytics_page()
        
    elif page == "📈 Comparison":
        from src.views.comparison import render_comparison_page
        render_comparison_page()
        
    elif page == "🛡️ Admin Dashboard":
        from src.views.admin_dashboard import show_admin_dashboard
        with db.get_session() as session:
            show_admin_dashboard(db, session)
            
    elif page == "🏁 Multi-Style":
        if st.session_state.get('user_tier') != 'admin':
            st.error("🔒 Admin Only")
        else:
            from src.views.multi_style_report import render_multi_style_report, run_multi_style_analysis
            st.title("🏁 Multi-Style Comparison")
            from src.utils_tickers import render_hybrid_ticker_input
            ms_ticker = render_hybrid_ticker_input(key_prefix="ms_report") or "AAPL"
            if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
                tickers = [t.strip().upper() for t in ms_ticker.split(",") if t.strip()]
                async def run_parallel_analysis(ticker_list, analyzer_inst):
                    # We create the coroutines INSIDE the async function so they are bound to the loop created by asyncio.run
                    tasks = [run_multi_style_analysis(t, analyzer_inst) for t in ticker_list]
                    return await asyncio.gather(*tasks)

                results = asyncio.run(run_parallel_analysis(tickers, analyzer))
                valid = [r for r in results if r]
                if valid:
                    st.session_state['ms_results'] = valid
                    st.session_state['ms_tickers'] = [r.ticker for r in valid]
            if 'ms_results' in st.session_state:
                render_multi_style_report(st.session_state['ms_results'])

if __name__ == "__main__":
    main()
