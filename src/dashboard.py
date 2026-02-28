"""
Streamlit Dashboard for Stock Analysis

Run with: streamlit run src/dashboard.py
"""

import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analyzer import StockAnalyzer, StockAnalysis
from src.database import Database
from src.models import Stock, Analysis
from src.visualization_tv import TVChartGenerator
from src.utils import save_analysis, render_ticker_header
from src.auth import AuthManager
from src.views.login import render_login_page
from src.theme_manager import ThemeManager


# Page configuration
st.set_page_config(
    page_title="Growth Investment Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Growth Investment Analyzer - Your personal AI-powered stock assistant."
    }
)

# Initialize database
@st.cache_resource
def init_database():
    """Initialize database connection"""
    db = Database("stock_analysis.db")
    db.init_db()
    
    # Self-healing migration: ensure theme_preference column exists (added after initial deployment)
    try:
        import sqlite3 as _sqlite3
        _conn = _sqlite3.connect("stock_analysis.db")
        _cur = _conn.cursor()
        _cur.execute("PRAGMA table_info(users)")
        _cols = [row[1] for row in _cur.fetchall()]
        if 'theme_preference' not in _cols and _cols:  # only if table exists
            _cur.execute("ALTER TABLE users ADD COLUMN theme_preference VARCHAR(20) DEFAULT 'dark'")
            _conn.commit()
        _conn.close()
    except Exception:
        pass  # Fresh DB will have the column from create_all()
    
    # Seed admin user if needed
    with db.get_session() as session:
        from src.auth import AuthManager
        AuthManager.seed_admin(session)
        
    return db


# Initialize analyzer
@st.cache_resource
def init_analyzer():
    """Initialize stock analyzer"""
    return StockAnalyzer()

# Initialize chart generator
@st.cache_resource
def init_chart_generator():
    """Initialize TV chart generator"""
    return TVChartGenerator()

# Initialize scheduler (for Streamlit Cloud support)
@st.cache_resource
def init_scheduler():
    """Start the background scheduler thread"""
    from src.scheduler import start_scheduler_thread
    start_scheduler_thread()
    return True


# Removed save_analysis_to_db and _safe_float - now in src.utils


def load_historical_analyses(db: Database, ticker: str, limit: int = 30):
    """Load historical analyses for a ticker"""
    session = db.SessionLocal()
    try:
        stock = session.query(Stock).filter(Stock.ticker == ticker).first()
        if not stock:
            return None
        
        analyses = session.query(Analysis).filter(
            Analysis.stock_id == stock.id
        ).order_by(Analysis.timestamp.desc()).limit(limit).all()
        
        if not analyses:
            return None
        
        # Convert to DataFrame
        data = []
        for a in analyses:
            data.append({
                'Date': a.timestamp,
                'Price': a.current_price,
                'RSI': a.rsi,
                'MACD': a.macd,
                'EMA20': a.ema20,
                'EMA50': a.ema50,
                'EMA200': a.ema200,
                'Sentiment': a.news_sentiment
            })
        
        return pd.DataFrame(data).sort_values('Date')
    finally:
        session.close()


async def analyze_stock(ticker: str):
    """Analyze a stock ticker"""
    analyzer = init_analyzer()
    return await analyzer.analyze(ticker, verbose=False)


def _safe_float_parse(val_str: str) -> Optional[float]:
    """Helper to parse finviz strings to float"""
    if not val_str or val_str == '-' or val_str == 'N/A':
        return None
    try:
        clean_str = val_str.replace('%', '').replace(',', '')
        if 'B' in clean_str:
            return float(clean_str.replace('B', '')) * 1e9
        if 'M' in clean_str:
            return float(clean_str.replace('M', '')) * 1e6
        return float(clean_str)
    except ValueError:
        return None

def render_checklist(analysis: StockAnalysis):
    """Render the Investment Checklist in the dashboard"""
    st.divider()
    st.subheader("✅ Investment Checklist")
    
    def _chk(text: str, passed: bool):
        icon = "✅" if passed else "⚠️"
        st.markdown(f"{icon} **{text}**")

    # 1. Market Cap >= 2B
    mc_str = analysis.finviz_data.get('Market Cap', '')
    mc_val = _safe_float_parse(mc_str)
    mc_pass = mc_val is not None and mc_val >= 2_000_000_000
    _chk(f"Market Cap >= 2 B? ({mc_str})", mc_pass)
    
    # 2. Listed on a US exchange?
    exchange = getattr(analysis, 'exchange', None)
    country = getattr(analysis, 'country', None)
    # Yahoo Finance exchange codes for US markets:
    # NMS/NGM/NCM = NASDAQ, NYQ/ASE = NYSE, PCX = NYSE Arca, BTS = BATS
    US_EXCHANGES = {
        'NMS', 'NGM', 'NCM',       # NASDAQ (Global Select, Global Market, Capital Market)
        'NYQ', 'ASE',               # NYSE, NYSE American (AMEX)
        'PCX',                      # NYSE Arca (ETFs, options)
        'BTS',                      # BATS / Cboe BZX
        'NasdaqGS', 'NasdaqGM', 'NasdaqCM',  # alternative codes
    }
    us_listed = (exchange in US_EXCHANGES) if exchange else (country in ['United States', 'USA'] if country else False)
    listing_label = f"exchange: {exchange}" if exchange else f"country: {country or 'N/A'}"
    _chk(f"Listed on US exchange? ({listing_label})", us_listed)
    
    # 3. Analyst recommendation Buy or Better
    rec = getattr(analysis, 'analyst_recommendation', '')
    rec_pass = rec in ['buy', 'strong_buy'] if rec else False
    _chk(f"Analyst recommendation Buy or Better? ({rec or 'N/A'})", rec_pass)
    
    # 4. Average volume >= 1M
    vol = getattr(analysis, 'average_volume', 0)
    vol_pass = vol is not None and vol >= 1_000_000
    vol_str = f"{int(vol):,}" if vol else "N/A"
    _chk(f"Average volume >= 1 million? ({vol_str})", vol_pass)
    
    # 5. ROE
    roe_str = analysis.finviz_data.get('ROE', '')
    roe_val = _safe_float_parse(roe_str)
    roe_good = roe_val is not None and roe_val >= 15
    roe_vgood = roe_val is not None and roe_val >= 20
    roe_badge = " ⭐ (Very Good)" if roe_vgood else ""
    _chk(f"ROE >= 15%{roe_badge} ({roe_str})", roe_good)
    
    # 6. ROA
    roa_str = analysis.finviz_data.get('ROA', '')
    roa_val = _safe_float_parse(roa_str)
    roa_good = roa_val is not None and roa_val >= 10
    roa_vgood = roa_val is not None and roa_val >= 20
    roa_badge = " ⭐ (Very Good)" if roa_vgood else ""
    _chk(f"ROA >= 10%{roa_badge} ({roa_str})", roa_good)
    
    # 7. EPS Growth
    eps_y_str = analysis.finviz_data.get('EPS this Y', '')
    eps_y_val = _safe_float_parse(eps_y_str)
    eps_y_good = eps_y_val is not None and eps_y_val >= 10
    eps_y_vgood = eps_y_val is not None and eps_y_val >= 20
    eps_y_badge = " ⭐ (Very Good)" if eps_y_vgood else ""
    _chk(f"EPS growth this year >= 10%{eps_y_badge} ({eps_y_str})", eps_y_good)
    
    eps_ny_str = analysis.finviz_data.get('EPS next Y', '')
    eps_ny_val = _safe_float_parse(eps_ny_str)
    eps_ny_good = eps_ny_val is not None and eps_ny_val >= 10
    eps_ny_vgood = eps_ny_val is not None and eps_ny_val >= 20
    eps_ny_badge = " ⭐ (Very Good)" if eps_ny_vgood else ""
    _chk(f"EPS growth next year >= 10%{eps_ny_badge} ({eps_ny_str})", eps_ny_good)
    
    eps_5y_str = analysis.finviz_data.get('EPS next 5Y', '')
    eps_5y_val = _safe_float_parse(eps_5y_str)
    eps_5y_good = eps_5y_val is not None and eps_5y_val >= 8
    eps_5y_vgood = eps_5y_val is not None and eps_5y_val >= 15
    eps_5y_badge = " ⭐ (Very Good)" if eps_5y_vgood else ""
    _chk(f"EPS growth 5 year >= 8%{eps_5y_badge} ({eps_5y_str})", eps_5y_good)
    
    # 8. Revenue & Earnings YoY
    rev_g = getattr(analysis, 'revenue_growth_yoy', None)
    op_g = getattr(analysis, 'op_income_growth_yoy', None)
    eps_g = getattr(analysis, 'eps_growth_yoy', None)
    
    rev_g_str = f"{rev_g*100:.2f}%" if rev_g is not None else "N/A"
    op_g_str = f"{op_g*100:.2f}%" if op_g is not None else "N/A"
    eps_g_str = f"{eps_g*100:.2f}%" if eps_g is not None else "N/A"
    
    rev_g_pass = rev_g is not None and rev_g >= 0.05
    op_g_pass = op_g is not None and op_g >= 0.05
    eps_g_pass = eps_g is not None and eps_g >= 0.10
    
    _chk(f"Revenue YoY growth >= 5%? ({rev_g_str})", rev_g_pass)
    _chk(f"Operating income YoY growth >= 5%? ({op_g_str})", op_g_pass)
    _chk(f"EPS (Diluted) YoY growth >= 10%? ({eps_g_str})", eps_g_pass)
    
    # 9. PE or PEG
    pe_str = analysis.finviz_data.get('P/E', '')
    pe_val = _safe_float_parse(pe_str)
    peg_str = analysis.finviz_data.get('PEG', '')
    peg_val = _safe_float_parse(peg_str)
    
    if peg_val is None and pe_val is not None and eps_5y_val is not None and eps_5y_val > 0:
        peg_val = pe_val / eps_5y_val
        peg_str = f"{peg_val:.2f} (calc)"
        
    pe_pass = pe_val is not None and pe_val <= 30
    peg_pass = peg_val is not None and peg_val <= 2
    
    _chk(f"P/E <= 30 ({pe_str}) OR PEG <= 2 ({peg_str})", pe_pass or peg_pass)
    
    # 10. Extras
    action = getattr(analysis, 'marketbeat_action_recent', None)
    next_earn = getattr(analysis, 'next_earnings_date', None)
    days_until = getattr(analysis, 'days_until_earnings', None)
    max_buy = getattr(analysis, 'max_buy_price', None)
    
    st.markdown("---")
    st.markdown(f"**🟢 Recent Analyst Upgrade/Downgrade:** {str(action) if action else 'N/A'}")
    
    if next_earn:
        try:
            date_str = next_earn.date() if hasattr(next_earn, 'date') else str(next_earn)[:10]
            days_str = f" (in {days_until} days)" if days_until and days_until > 0 else ""
            st.markdown(f"**📅 Next Quarter Earnings Date:** {date_str}{days_str}")
        except Exception:
            st.markdown(f"**📅 Next Quarter Earnings Date:** {str(next_earn)[:10]}")
    else:
        st.markdown("**📅 Next Quarter Earnings Date:** N/A")
        
    st.markdown(f"**💵 Max Buy Price (Median Target / 1.15):** ${max_buy:.2f}" if max_buy else "**💵 Max Buy Price:** N/A")
    st.divider()



def main():
    """Main dashboard application"""
    
    # Initialize resources
    db = init_database()
    chart_gen = init_chart_generator()
    init_scheduler()  # Start background scheduler
    
    # Initialize session state for auth
    AuthManager.init_session_state()
    
    # Store in session state
    if 'db' not in st.session_state:
        st.session_state['db'] = db
        
    # Authentication Gate
    if not AuthManager.is_authenticated():
        render_login_page()
        return
        
    # Hook the global theme config early to prevent UI flickering and double-renders
    # ThemeManager.apply_theme()
    ThemeManager.inject_custom_css()
    
    # Sidebar navigation
    with st.sidebar:
        st.title("📊 Stock Analyzer")
        
        # Add personalized greeting and Theme Manager
        st.markdown(f"**Hello, {st.session_state.get('username', 'User')}!** 👋")
        
        # Theme configuration
        current_theme = st.session_state.get('theme_preference', 'dark')
        theme_options = ['dark', 'light']
        theme_index = theme_options.index(current_theme) if current_theme in theme_options else 0
        
        selected_theme = st.selectbox(
            "🎨 UI Theme",
            options=theme_options,
            index=theme_index,
            format_func=lambda x: "☀️ Light Mode" if x == 'light' else "🌙 Dark Mode"
        )
        
        if selected_theme != current_theme:
            with st.spinner("Updating theme..."):
                with db.get_session() as session:
                    if AuthManager.update_theme(session, st.session_state['user_id'], selected_theme):
                        st.session_state['theme_preference'] = selected_theme
                        st.rerun()

        st.divider()
        
        tier = st.session_state.get('user_tier', 'free')
        nav_options = [
            "🏠 Home",
            "💼 Portfolio",
            "📋 Watchlist",
            "🔔 Alerts",
            "📈 Comparison",
            "🧪 Backtester",
            "🌊 Options Flow"
        ]
        
        # Premium and Admin Only Features
        if tier in ['premium', 'admin']:
            nav_options.extend([
                "🌍 Market Pulse",
                "🔍 Screener",
                "🔬 Advanced Analytics"
            ])
            
        if tier == 'admin':
            nav_options.append("🛡️ Admin Dashboard")

        # Programmatic navigation: directly set nav_radio session state key so
        # st.radio picks it up (index= is ignored when the key already exists in state)
        if 'go_to_page' in st.session_state:
            target_page = st.session_state.pop('go_to_page')
            if target_page in nav_options:
                st.session_state['nav_radio'] = target_page
            
        page = st.radio("Navigation", options=nav_options, key="nav_radio")
        
        # Upsell for free users
        if tier == 'free':
            st.info("⭐ Upgrade to Premium to unlock the Market Pulse, automated AI Screener, and Advanced Analytics!")
        
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            AuthManager.logout()
            
    # Route to selected page
    if page == "🌍 Market Pulse":
        from src.views.market_pulse import render_market_pulse_page
        render_market_pulse_page()
        return

    elif page == "🔍 Screener":
        from src.views.screener import render_screener_page
        render_screener_page()
        return

    elif page == "💼 Portfolio":
        from src.views.portfolio_tracker import render_portfolio_tracker_page
        render_portfolio_tracker_page()
        return

    elif page == "🧪 Backtester":
        from src.views.backtest import render_backtesting_page
        render_backtesting_page()
        return

    elif page == "🌊 Options Flow":
        from src.views.options_flow import render_options_flow_page
        render_options_flow_page()
        return

    elif page == "📋 Watchlist":
        from src.views.watchlist import render_watchlist_page
        render_watchlist_page()
        return
    
    elif page == "🔔 Alerts":
        from src.views.alerts import render_alerts_page
        render_alerts_page()
        return
    
    elif page == "🔬 Advanced Analytics":
        from src.views.advanced_analytics import render_advanced_analytics_page
        render_advanced_analytics_page()
        return
        
    elif page == "🛡️ Admin Dashboard":
        from src.views.admin_dashboard import show_admin_dashboard
        # The admin dashboard signature needs db and session.
        # Let's initialize a session specifically for it or modify the function signature.
        from src.database import Database
        db = Database()
        with db.get_session() as session:
            show_admin_dashboard(db, session)
        return
    elif page == "📈 Comparison":
        from src.views.comparison import render_comparison_page
        render_comparison_page()
        return
    
    # Home page (original dashboard)
    st.title("📊 Growth Investment Analyzer")
    st.markdown("Comprehensive stock analysis with technical indicators, fundamentals, and sentiment analysis")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Ticker History Dropdown
        db_tickers = db.get_all_tickers()
        if db_tickers:
            selected_history = st.selectbox(
                "Search History",
                options=["Enter New..."] + db_tickers,
                index=0,
                help="Select a previously analyzed stock"
            )
            # Pre-fill ticker input if something is selected from history
            default_ticker = selected_history if selected_history != "Enter New..." else "AAPL"
        else:
            default_ticker = "AAPL"
            
        from src.utils_tickers import render_hybrid_ticker_input
        ticker = render_hybrid_ticker_input(key_prefix="main_dash")
        if not ticker:
            ticker = default_ticker
            
        analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)
        
        st.divider()
        st.divider()
        st.caption("Data sources: Yahoo Finance, Finviz, MarketBeat")
        
        st.divider()
        with st.expander("🔧 System"):
            if st.button("Clear Cache & Reload", type="secondary"):
                st.cache_resource.clear()
                st.cache_data.clear()
                st.rerun()
    
    # Main content
    if analyze_button and ticker:
        with st.spinner(f"Analyzing {ticker}..."):
            try:
                # Run async analysis
                analysis = asyncio.run(analyze_stock(ticker))
                
                if analysis:
                    # Save to database
                    save_analysis(db, analysis)
                    
                    # Display header with name, timestamp, and links
                    render_ticker_header(analysis)
                    
                    # Earnings Warning (if applicable)
                    if analysis.has_earnings_warning():
                        st.warning(f"⚠️ **Earnings Alert:** Next earnings in {analysis.days_until_earnings} days ({analysis.next_earnings_date.date()}) - Trade with caution!")
                    
                    # Key Metrics Row
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        st.metric("Current Price", f"${analysis.current_price:.2f}")
                    with col2:
                        if analysis.median_price_target:
                            upside = ((analysis.median_price_target - analysis.current_price) / analysis.current_price) * 100
                            st.metric("Price Target", f"${analysis.median_price_target:.2f}", f"{upside:+.1f}%")
                        else:
                            st.metric("Price Target", "N/A")
                    with col3:
                        st.metric("RSI (14)", f"{analysis.rsi:.1f}")
                    with col4:
                        st.metric("ATR (14)", f"{analysis.atr:.2f}")
                    with col5:
                        if analysis.news_sentiment:
                            sentiment_label = "Positive" if analysis.news_sentiment > 0.1 else "Negative" if analysis.news_sentiment < -0.1 else "Neutral"
                            st.metric("Sentiment", sentiment_label, f"{analysis.news_sentiment:.2f}")
                        else:
                            st.metric("Sentiment", "N/A")
                    
                    # Trend Badge
                    if hasattr(analysis, 'market_trend') and analysis.market_trend:
                        trend_color = "green" if analysis.market_trend == "Uptrend" else "red" if analysis.market_trend == "Downtrend" else "gray"
                        st.markdown(f"### Market Trend: :{trend_color}[{analysis.market_trend}]")
                        
                    # Show Investment Checklist
                    render_checklist(analysis)
                    
                    # AI-Powered Trade Thesis
                    st.divider()
                    st.subheader("🤖 AI Investment Thesis")
                    from src.ai_analyzer import AIAnalyzer
                    
                    # Create data payload for the prompt from the analysis object
                    ai_payload = {
                        "current_price": analysis.current_price,
                        "trend": getattr(analysis, 'market_trend', 'Unknown'),
                        "support": getattr(analysis, 'support_levels', [None])[-1] if getattr(analysis, 'support_levels', []) else 'Unknown',
                        "resistance": getattr(analysis, 'resistance_levels', [None])[0] if getattr(analysis, 'resistance_levels', []) else 'Unknown',
                        "hvn": getattr(analysis, 'volume_profile_hvns', [None])[-1] if getattr(analysis, 'volume_profile_hvns', []) else 'Unknown',
                    }
                    if analysis.news_sentiment is not None:
                        sentiment_label = "Positive" if analysis.news_sentiment > 0.1 else "Negative" if analysis.news_sentiment < -0.1 else "Neutral"
                        ai_payload["sentiment"] = {"score": analysis.news_sentiment, "label": sentiment_label}
                        
                    # Call AI Analyzer directly on the main dashboard thread
                    with st.spinner("Generating AI Analysis..."):
                        ai_engine = AIAnalyzer()
                        if ai_engine.is_available():
                            thesis_text = ai_engine.generate_thesis(analysis.ticker, ai_payload)
                            st.info(thesis_text)
                        else:
                            st.warning("⚠️ AI Analysis is currently unavailable. Please configure your `GEMINI_API_KEY` in Streamlit secrets or OS environment.")
                            
                    # 🎯 Professional Trade Execution Setup
                    st.divider()
                    st.subheader("🎯 Trade Execution Setup")
                    
                    # Create a prominent container for the trade setup
                    with st.container(border=True):
                        # Top Metrics Row
                        col_e, col_sl, col_rr = st.columns(3)
                        
                        raw_entry = getattr(analysis, "suggested_entry", None)
                        raw_stop = getattr(analysis, "suggested_stop_loss", None)
                        raw_target = analysis.median_price_target
                        
                        with col_e:
                            entry_val = f"${float(raw_entry):.2f}" if raw_entry is not None else "WAIT"
                            st.metric("Suggested Entry", entry_val, help="Risk-adjusted entry point above clusters.")
                            
                        with col_sl:
                            stop_val = f"${float(raw_stop):.2f}" if raw_stop is not None else "N/A"
                            st.metric("Stop Loss", stop_val, delta_color="inverse", help="ATR-adjusted exit point.")
                            
                        with col_rr:
                            if raw_entry and raw_stop and raw_target:
                                rr = (raw_target - raw_entry) / (raw_entry - raw_stop)
                                rr_color = "normal" if rr >= 2.0 else "off"
                                st.metric("Risk/Reward Ratio", f"{rr:.2f}x", delta="Target Reachable" if rr >= 2.0 else "Low R/R", delta_color=rr_color)
                            else:
                                st.metric("Risk/Reward Ratio", "N/A")

                        st.divider()
                        
                        # Logic and S/R Details
                        col_logic, col_levels = st.columns([1, 1.2])
                        
                        with col_logic:
                            st.markdown("#### 🧮 Decision Matrix")
                            setup_notes = getattr(analysis, "setup_notes", [])
                            if setup_notes:
                                for note in setup_notes:
                                    if "✅" in note: st.success(note)
                                    elif "⚠️" in note: st.warning(note)
                                    elif "❌" in note: st.error(note)
                                    else: st.info(note)
                            else:
                                st.info("Waiting for trend confirmation...")

                        with col_levels:
                            st.markdown("#### 🏛️ Institutional Levels")
                            l_col1, l_col2 = st.columns(2)
                            
                            raw_support = getattr(analysis, "support_levels", [])
                            raw_resist = getattr(analysis, "resistance_levels", [])
                            raw_hvns = getattr(analysis, "volume_profile_hvns", [])
                            
                            with l_col1:
                                st.write("**Support Zones**")
                                if raw_support:
                                    for s in raw_support[:2]: st.code(f"${float(s):.2f}")
                                hvn_supp = [h for h in raw_hvns if analysis.current_price and h < analysis.current_price]
                                if hvn_supp:
                                    st.write("*Vol Profile HVN:*")
                                    st.code(f"${float(max(hvn_supp)):.2f}")
                                    
                            with l_col2:
                                st.write("**Resistance Zones**")
                                if raw_resist:
                                    for r in raw_resist[:2]: st.code(f"${float(r):.2f}")
                                hvn_res = [h for h in raw_hvns if analysis.current_price and h > analysis.current_price]
                                if hvn_res:
                                    st.write("*Vol Profile HVN:*")
                                    st.code(f"${float(min(hvn_res)):.2f}")
                                    
                        # Expandable mathematical background
                        with st.expander("Show Calculation Logic"):
                            st.markdown(
                                """
                                **Support & Resistance:** Found using **Volume Profile (Price by Volume)** to identify heavily traded zones (HVNs) and **Statistical 1D Clustering** to group nearby price extrema.
                                **Suggested Entry:** Calculated as **0.5%** above the nearest Support level with rounding adjustments to avoid institutional piling.
                                **Suggested Stop Loss:** Calculated as **Nearest Support - 1 Average True Range (ATR)**.
                                """
                            )
                        
                    # OHLC Details
                    st.subheader("📊 Price Details")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Open", f"${analysis.open:.2f}")
                    with col2:
                        st.metric("High", f"${analysis.high:.2f}")
                    with col3:
                        st.metric("Low", f"${analysis.low:.2f}")
                    with col4:
                        st.metric("Close", f"${analysis.close:.2f}")
                    
                    # Earnings & Financials
                    if analysis.next_earnings_date or analysis.revenue:
                        st.subheader("💼 Earnings & Financials")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            if analysis.next_earnings_date:
                                st.write(f"**Next Earnings:** {analysis.next_earnings_date.date()}")
                                st.write(f"*({analysis.days_until_earnings} days)*")
                            else:
                                st.write("**Next Earnings:** N/A")
                        
                        with col2:
                            if pd.notna(analysis.revenue):
                                revenue_b = analysis.revenue / 1e9
                                st.write(f"**Revenue (Q):** ${revenue_b:.2f}B")
                            else:
                                st.write("**Revenue (Q):** N/A")
                        
                        with col3:
                            if pd.notna(analysis.operating_income):
                                op_income_b = analysis.operating_income / 1e9
                                st.write(f"**Op Income (Q):** ${op_income_b:.2f}B")
                            else:
                                st.write("**Op Income (Q):** N/A")
                        
                        with col4:
                            if pd.notna(analysis.basic_eps):
                                st.write(f"**EPS (Q):** ${analysis.basic_eps:.2f}")
                            else:
                                st.write("**EPS (Q):** N/A")
                    
                    # Technical Indicators & Chart
                    st.subheader("📈 Technical Chart")
                    
                    # Moved Inline Chart Controls here
                    st.markdown("##### Chart Controls")
                    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns(4)
                    
                    with ctrl1:
                        show_ema = st.checkbox("Show EMAs", value=True, key="chk_ema")
                        show_atr = st.checkbox("Show ATR", value=False, key="chk_atr")
                    with ctrl2:
                        show_support_resistance = st.checkbox("Support/Resistance", value=True, key="chk_sr")
                        show_trade_setup = st.checkbox("Entry/Stop", value=True, key="chk_ts")
                    with ctrl3:
                        show_rsi = st.checkbox("Show RSI", value=True, key="chk_rsi")
                        show_macd = st.checkbox("Show MACD", value=True, key="chk_macd")
                    with ctrl4:
                        show_bollinger = st.checkbox("Show BOLL", value=False, key="chk_boll")
                    
                    # Generate unified interactive chart
                    chart_gen.generate_candlestick_chart(
                        analysis,
                        show_ema=show_ema,
                        show_atr=show_atr,
                        show_rsi=show_rsi,
                        show_macd=show_macd,
                        show_bollinger=show_bollinger,
                        show_support_resistance=show_support_resistance,
                        show_trade_setup=show_trade_setup,
                        height=600 if show_rsi or show_macd else 500
                    )
                    
                    # Fundamental Data
                    st.subheader("💰 Fundamental Data")
                    if analysis.finviz_data:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write("**Valuation**")
                            st.write(f"Market Cap: {analysis.finviz_data.get('Market Cap', 'N/A')}")
                            st.write(f"P/E: {analysis.finviz_data.get('P/E', 'N/A')}")
                            st.write(f"PEG: {analysis.finviz_data.get('PEG', 'N/A')}")
                        
                        with col2:
                            st.write("**Profitability**")
                            st.write(f"ROE: {analysis.finviz_data.get('ROE', 'N/A')}")
                            st.write(f"ROA: {analysis.finviz_data.get('ROA', 'N/A')}")
                            st.write(f"Inst Own: {analysis.finviz_data.get('Inst Own', 'N/A')}")
                        
                        with col3:
                            st.write("**Growth**")
                            st.write(f"EPS This Y: {analysis.finviz_data.get('EPS this Y', 'N/A')}")
                            st.write(f"EPS Next Y: {analysis.finviz_data.get('EPS next Y', 'N/A')}")
                            st.write(f"EPS Next 5Y: {analysis.finviz_data.get('EPS next 5Y', 'N/A')}")
                    
                    # Sentiment Analysis Summary
                    if analysis.news_summary:
                        st.divider()
                        st.subheader("📰 Sentiment Analysis & News")
                        st.info(analysis.news_summary)
                    
                    # Historical Trend
                    st.subheader("📊 Historical Analysis")
                    hist_df = load_historical_analyses(db, ticker)
                    if hist_df is not None and len(hist_df) > 1:
                        st.line_chart(hist_df.set_index('Date')[['Price', 'RSI']])
                    else:
                        st.info("Run multiple analyses over time to see historical trends")
                    
                else:
                    st.error(f"Failed to analyze {ticker}. Please check the ticker symbol.")

            except Exception as e:
                st.error(f"An error occurred while analyzing {ticker}: {e}")
                st.expander("Detailed Error Trace").write(e)
    
    else:
        st.info("👈 Enter a ticker symbol and click 'Analyze' to get started")


if __name__ == "__main__":
    main()
