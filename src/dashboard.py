"""
Streamlit Dashboard for Stock Analysis

Run with: streamlit run src/dashboard.py
"""

import streamlit as st
import asyncio
import plotly.graph_objects as go
import plotly.express as px
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
from src.utils import save_analysis, render_ticker_header, _safe_float_parse
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
    
    # Self-healing migration: ensure theme_preference and show_hvn columns exist
    try:
        import sqlite3 as _sqlite3
        _conn = _sqlite3.connect("stock_analysis.db")
        _cur = _conn.cursor()
        _cur.execute("PRAGMA table_info(users)")
        _cols = [row[1] for row in _cur.fetchall()]
        if _cols:  # only if table exists
            if 'theme_preference' not in _cols:
                _cur.execute("ALTER TABLE users ADD COLUMN theme_preference VARCHAR(20) DEFAULT 'dark'")
            if 'show_hvn' not in _cols:
                _cur.execute("ALTER TABLE users ADD COLUMN show_hvn INTEGER DEFAULT 1")
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


async def analyze_stock(ticker: str, trading_style: str = "Growth Investing"):
    """Analyze a stock ticker"""
    analyzer = init_analyzer()
    # Debug: print signature to console/logs
    try:
        import inspect
        sig = inspect.signature(analyzer.analyze)
        print(f"[DEBUG] analyzer.analyze signature: {sig}")
    except Exception:
        pass
    return await analyzer.analyze(ticker, trading_style_name=trading_style, verbose=False)


# Removed _safe_float_parse - now in src.utils

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
        
    if max_buy:
        st.markdown(f"**💵 Max Buy Price (Analyst Target ÷ 1.15):** ${max_buy:.2f}")
    else:
        # MBP is None — stock is trading above the analyst consensus target
        matp = getattr(analysis, 'median_price_target', None)
        price = getattr(analysis, 'current_price', None)
        if matp and price and price > matp:
            st.warning(
                f"⚠️ **Above Analyst Targets:** Current price (${price:.2f}) exceeds analyst consensus "
                f"target (${matp:.2f}). No valid Max Buy Price — the stock has outrun analyst estimates. "
                f"Consider waiting for a consolidation or updated targets."
            )
        else:
            st.markdown("**💵 Max Buy Price:** N/A")
    st.divider()



def main():
    """Main dashboard application"""
    
    # Initialize resources
    db = init_database()
    chart_gen = init_chart_generator()
    init_scheduler()  # Start background scheduler
    
    # Initialize session state for auth
    AuthManager.init_session_state()
    
    # Initialize session state for chart preferences (local UI state)
    if 'chart_prefs' not in st.session_state:
        st.session_state['chart_prefs'] = {
            'ema': True,
            'atr': True,
            'sr': True,
            'ts': True,
            'rsi': False,
            'macd': False,
            'boll': False
        }
    
    # Store in session state
    if 'db' not in st.session_state:
        st.session_state['db'] = db
        
    # Authentication Gate
    if not AuthManager.is_authenticated():
        render_login_page()
        return
        
    # Hook the global theme config early to prevent UI flickering and double-renders
    ThemeManager.apply_theme()
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
            nav_options.append("🏁 Multi-Style")
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
    
    elif page == "🏁 Multi-Style":
        # ── Admin-only gate ──────────────────────────────────────────────
        if st.session_state.get('user_tier') != 'admin':
            st.error("🔒 Multi-Style Analysis is currently available to admin users only.")
            st.info("Contact the administrator to request access.")
            return
        # ─────────────────────────────────────────────────────────────────
        from src.views.multi_style_report import render_multi_style_report, run_multi_style_analysis
        
        st.title("🏁 Multi-Style Strategy Comparison")
        st.markdown("Run all trading styles simultaneously to find the best setup for any ticker.")
        
        from src.utils_tickers import render_hybrid_ticker_input
        ms_ticker = render_hybrid_ticker_input(key_prefix="ms_report") or "AAPL"
        
        if st.button("🚀 Run Multi-Style Analysis", type="primary", use_container_width=True):
            # Split by comma and clean up
            tickers = [t.strip().upper() for t in ms_ticker.split(",") if t.strip()]
            if not tickers:
                st.error("Please enter at least one ticker.")
            else:
                with st.spinner(f"Running comprehensive analysis for {', '.join(tickers)}..."):
                    analyzer = init_analyzer()
                    
                    async def run_all(ticker_list):
                        tasks = [run_multi_style_analysis(t, analyzer) for t in ticker_list]
                        return await asyncio.gather(*tasks)
                    
                    results = asyncio.run(run_all(tickers))
                    # Filter out None results (failures)
                    valid_results = [r for r in results if r]
                    
                    if valid_results:
                        st.session_state['ms_results'] = valid_results
                        st.session_state['ms_tickers'] = [r.ticker for r in valid_results]
                    else:
                        st.error(f"Failed to analyze any of the tickers: {ms_ticker}")
        
        if 'ms_results' in st.session_state:
            # Check if any original ticker is still relevant (simple check)
            if any(t in ms_ticker.upper() for t in st.session_state.get('ms_tickers', [])):
                render_multi_style_report(st.session_state['ms_results'])
        return
    
    # Home page (original dashboard)
    # The title must be rendered *after* the sidebar processes the trading style selection to prevent 1-click lag

    
    # Sidebar
    with st.sidebar:
        from src import __version__
        st.caption(f"v{__version__}")
        
        # Deployment Debugger
        with st.expander("🔍 Debug Deployment"):
            import os, datetime
            for fname in ["src/analyzer.py", "src/models.py", "src/dashboard.py"]:
                try:
                    mtime = os.path.getmtime(fname)
                    dt = datetime.datetime.fromtimestamp(mtime)
                    st.text(f"{fname.split('/')[-1]}: {dt.strftime('%H:%M:%S')}")
                except:
                    st.text(f"{fname}: Error")
                    
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
            
        st.divider()
        st.subheader("📈 Trading Strategy")
        
        # Access control for premium trading styles
        can_swing = (
            st.session_state.get('can_use_swing_trading', False)
            or st.session_state.get('user_tier') in ('admin', 'premium')
        )
        can_trend = st.session_state.get('user_tier') in ('admin', 'premium')
        
        style_options = ["Growth Investing", "Swing Trading", "Trend Trading"]
        
        # Determine the default index for the selectbox based on session state
        current_active_style = st.session_state.get('active_trading_style', "Growth Investing")
        default_index = style_options.index(current_active_style) if current_active_style in style_options else 0
        
        selected_style = st.selectbox(
            "Select Style",
            options=style_options,
            index=default_index,
            help="Choose your investment/trading strategy"
        )
        
        
        if selected_style == "Swing Trading" and not can_swing:
            st.warning("🔒 Swing Trading is a premium feature. Upgrade your account for access.")
            analyze_disabled = True
        elif selected_style == "Trend Trading" and not can_trend:
            st.warning("🔒 Trend Trading is a premium feature. Upgrade your account for access.")
            analyze_disabled = True
        else:
            analyze_disabled = False
            
            # Apply Style Defaults if style changed
            if 'active_trading_style' not in st.session_state or st.session_state['active_trading_style'] != selected_style:
                from src.trading_styles.factory import get_trading_style
                style_strategy = get_trading_style(selected_style)
                defaults = style_strategy.get_chart_defaults()
                st.session_state['chart_prefs'].update({
                    'ema': defaults.get('ema', True),
                    'atr': defaults.get('atr', True),
                    'sr': defaults.get('sr', True),
                    'ts': defaults.get('ts', True),
                    'rsi': defaults.get('rsi', False),
                    'macd': defaults.get('macd', False),
                    'boll': defaults.get('boll', False)
                })
                # Set timeframe and zoom from strategy defaults
                st.session_state['timeframe'] = defaults.get('timeframe', 'D')
                st.session_state['zoom'] = defaults.get('zoom', '1Y')
                
                st.session_state['active_trading_style'] = selected_style
                
                # Clear current analysis to prevent state leaking between styles
                if 'current_analysis' in st.session_state:
                    del st.session_state['current_analysis']
                
                # Log the style change
                _uid = st.session_state.get('user_id')
                if _uid and db:
                    from src.activity_logger import log_activity
                    log_activity(db, _uid, "Trading Style", f"switch_to_{selected_style.lower().replace(' ', '_')}")
            
        analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True, disabled=analyze_disabled)
        
        st.divider()
        st.divider()
        st.caption("Data sources: Yahoo Finance, Finviz, MarketBeat")
        
        st.divider()
        with st.expander("🔧 System"):
            if st.button("Clear Cache & Reload", type="secondary"):
                st.cache_resource.clear()
                st.cache_data.clear()
                st.rerun()
                
    # Now render the dynamic title AFTER the sidebar state has been established
    selected_style = st.session_state.get('active_trading_style', "Growth Investing")
    st.title(f"📊 {selected_style} Analyzer")
    st.markdown("Comprehensive stock analysis with technical indicators, fundamentals, and sentiment analysis")
    
    # Main content
    if analyze_button and ticker:
        with st.spinner(f"Analyzing {ticker}..."):
            try:
                # Run async analysis
                fetched_analysis = asyncio.run(analyze_stock(ticker, selected_style))
                
                if fetched_analysis:
                    # Save to database
                    save_analysis(db, fetched_analysis)
                    st.session_state['current_analysis'] = fetched_analysis
                    st.session_state['current_ticker'] = ticker
                    
                    # ── In-App Alert Notifications ─────────────────────────────────────
                    try:
                        from src.alerts.alert_engine import AlertEngine
                        alert_engine = AlertEngine(use_email=False)
                        with db.get_session() as alert_session:
                            triggered = alert_engine.check_alerts(alert_session, fetched_analysis)
                            for t in triggered:
                                atype = t.get('alert_type', '').upper()
                                cond  = t.get('condition', '')
                                val   = t.get('current_value', 0)
                                thr   = t.get('threshold', 0)
                                icon  = "🚨" if cond in ('crosses_above', 'crosses_below') else "🔔"
                                condition_str = cond.replace('_', ' ')
                                st.toast(
                                    f"{icon} **{ticker} Alert!** {atype} {condition_str} {thr:.2f} — current: {val:.2f}",
                                    icon="⚠️"
                                )
                    except Exception as _ae:
                        pass  # Alerts are non-critical; don't break the main flow
                    # ─────────────────────────────────────────────────────────────────
                    
                    # Log activity
                    _uid = st.session_state.get('user_id')
                    if _uid:
                        from src.activity_logger import log_activity
                        log_activity(db, _uid, "Dashboard", f"analyze_{selected_style.lower().replace(' ', '_')}", ticker=ticker)
                else:
                    st.error(f"Failed to analyze {ticker}. Please check the ticker symbol.")
            except Exception as e:
                st.error(f"An error occurred while analyzing {ticker}: {e}")
                st.expander("Detailed Error Trace").write(e)

    if True:
        if st.session_state.get('current_analysis') and st.session_state.get('current_ticker') == ticker:
            try:
                if True:
                    analysis = st.session_state['current_analysis']
                    
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
                        # Force "Trend Trading" to use ATR (14d) and analysis.atr_daily
                        is_trend_or_swing = (selected_style in ["Swing Trading", "Trend Trading"]) or (analysis.trading_style in ["Swing Trading", "Trend Trading"])
                        atr_val = getattr(analysis, 'atr_daily', analysis.atr) if is_trend_or_swing else analysis.atr
                        atr_label = "ATR (14d)" if is_trend_or_swing else "ATR (14w)"
                        st.metric(atr_label, f"{atr_val:.2f}")
                    with col5:
                        if analysis.trading_style == "Swing Trading" and getattr(analysis, 'target_price', None):
                            upside_swing = ((analysis.target_price - analysis.current_price) / analysis.current_price) * 100
                            st.metric("PT", f"${analysis.target_price:.2f}", f"{upside_swing:+.1f}%")
                        elif analysis.news_sentiment:
                            sentiment_label = "Positive" if analysis.news_sentiment > 0.1 else "Negative" if analysis.news_sentiment < -0.1 else "Neutral"
                            st.metric("Sentiment", sentiment_label, f"{analysis.news_sentiment:.2f}")
                        else:
                            st.metric("Sentiment", "N/A")
                    
                    # Trend Badge
                    if hasattr(analysis, 'market_trend') and analysis.market_trend:
                        trend_color = "green" if analysis.market_trend == "Uptrend" else "red" if analysis.market_trend == "Downtrend" else "gray"
                        st.markdown(f"### Market Trend: :{trend_color}[{analysis.market_trend}]")
                        
                    # Show Investment Checklist ONLY for Growth Investing
                    # Use both selected_style and analysis.trading_style for absolute certainty
                    if selected_style == "Growth Investing" and analysis.trading_style == "Growth Investing":
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
                        col_e, col_sl = st.columns(2)
                        
                        raw_entry = getattr(analysis, "suggested_entry", None)
                        raw_stop = getattr(analysis, "suggested_stop_loss", None)
                        raw_target = analysis.median_price_target
                        
                        with col_e:
                            entry_val = f"${float(raw_entry):.2f}" if raw_entry is not None else "WAIT"
                            st.metric("Suggested Entry", entry_val, help="Risk-adjusted entry point above clusters.")
                            
                        with col_sl:
                            stop_val = f"${float(raw_stop):.2f}" if raw_stop is not None else "N/A"
                            st.metric("Stop Loss", stop_val, delta_color="inverse", help="ATR-adjusted exit point.")

                        if analysis.trading_style in ["Swing Trading", "Trend Trading"] and getattr(analysis, 'reward_to_risk', None):
                            st.divider()
                            col_rr, col_pt = st.columns(2)
                            with col_rr:
                                rr_val = analysis.reward_to_risk
                                threshold = 3.0 if analysis.trading_style == "Trend Trading" else 2.0
                                rr_color = "normal" if rr_val >= threshold else "inverse"
                                st.metric("Reward/Risk Ratio", f"{rr_val:.2f}x", delta=f">= {threshold:.1f}x required", delta_color=rr_color)
                            with col_pt:
                                target_val = f"${float(analysis.target_price):.2f}" if getattr(analysis, 'target_price', None) else "N/A"
                                st.metric("PT", target_val)

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
                                buy_score = getattr(analysis, 'buy_score', None)
                                if buy_score is not None:
                                    st.metric("Probability Score", f"{buy_score:.0%}")
                            else:
                                st.info("Waiting for trend confirmation...")
                                
                            if analysis.trading_style == "Swing Trading":
                                st.markdown("#### ✅ Strategy Validation")
                                has_patterns = len(getattr(analysis, 'swing_patterns', [])) > 0
                                rr_ratio = getattr(analysis, 'reward_to_risk', 0)
                                trend = getattr(analysis, 'market_trend', 'Unknown')
                                
                                # Trend Check
                                trend_icon = "🟢" if trend in ["Uptrend", "Sideways", "Downtrend"] else "🔴"
                                st.write(f"{trend_icon} **Trend:** {trend}")
                                
                                # Pattern Check
                                pat_icon = "🟢" if has_patterns else "🔴"
                                st.write(f"{pat_icon} **Pattern:** {'Confirmed' if has_patterns else 'None Detected'}")
                                
                                # R/R Check
                                rr_icon = "🟢" if rr_ratio >= 2.0 else "🔴"
                                st.write(f"{rr_icon} **Reward/Risk:** {rr_ratio:.1f}x (Req: 2.0x)")

                            if analysis.trading_style == "Swing Trading" and getattr(analysis, 'swing_patterns', []):
                                st.markdown("#### 📉 Pattern Confirmation")
                                for idx, pattern in enumerate(analysis.swing_patterns[:2]): # Show top 2
                                    with st.container(border=True):
                                        st.caption(f"**P{idx+1}: {pattern['pattern']}** at ${pattern['level']:.2f}")
                                        
                                        plot_df = pattern['plot_data']
                                        level = float(pattern['level'])
                                        
                                        fig = go.Figure()
                                        
                                        # Price Line
                                        fig.add_trace(go.Scatter(
                                            x=plot_df.index, y=plot_df['Close'],
                                            name="Price", line=dict(color='#2196F3', width=2),
                                            mode='lines'
                                        ))
                                        
                                        # Level Line (Solid Black/White for S, Solid Red for R)
                                        is_support = "Support" in pattern['pattern']
                                        theme = st.session_state.get('theme_preference', 'dark')
                                        s_color = '#FFFFFF' if theme == 'dark' else '#000000'
                                        line_color = s_color if is_support else '#FF0000'
                                        line_name = 'S' if is_support else 'R'
                                        
                                        fig.add_trace(go.Scatter(
                                            x=plot_df.index, y=[level] * len(plot_df),
                                            name=line_name, line=dict(color=line_color, width=2, dash='solid'),
                                            mode='lines+text',
                                            text=[line_name] + [''] * (len(plot_df) - 1),
                                            textposition="top right",
                                            textfont=dict(color=line_color, size=14, family="Arial Black")
                                        ))
                                        
                                        # Calculate dynamic padding based on actual data range
                                        prices = plot_df['Close'].tolist()
                                        p_min, p_max = min(prices), max(prices)
                                        # Use the wider range: either the price action range or the distance to the level
                                        data_range = max(p_max - p_min, abs(p_max - level), abs(level - p_min))
                                        if data_range == 0: data_range = level * 0.01 # Fallback
                                        
                                        # Add 20% padding to the top and bottom of the visible range
                                        padding = data_range * 0.20
                                        y_min = min(p_min, level) - padding
                                        y_max = max(p_max, level) + padding
                                        
                                        fig.update_layout(
                                            height=180,
                                            margin=dict(l=10, r=10, t=10, b=10),
                                            showlegend=False,
                                            xaxis=dict(showgrid=False, rangeslider=dict(visible=False), showticklabels=False),
                                            yaxis=dict(range=[y_min, y_max], showgrid=True, gridcolor='rgba(128,128,128,0.1)'),
                                            paper_bgcolor='rgba(0,0,0,0)',
                                            plot_bgcolor='rgba(0,0,0,0)',
                                        )
                                        
                                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

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
                                **Suggested Entry:** Calculated as **0.35%** buffer above/below Support/Resistance based on trend.
                                **Suggested Stop Loss:** Calculated using **ATR ({'14d' if analysis.trading_style in ['Swing Trading', 'Trend Trading'] else '14w'})**.
                                **Reward/Risk:** Minimum **{'3.0x' if analysis.trading_style == 'Trend Trading' else '2.0x'}** requirement enforced for valid setups. If the immediate level does not provide a 3.0x/2.0x R/R, the engine evaluates historical deeper support/resistance levels.
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
                        show_ema = st.checkbox("Show EMAs", value=st.session_state['chart_prefs']['ema'], key="chk_ema")
                        atr_label = "Show ATR (14d)" if analysis.trading_style in ["Swing Trading", "Trend Trading"] else "Show ATR (14w)"
                        show_atr = st.checkbox(atr_label, value=st.session_state['chart_prefs']['atr'], key="chk_atr")
                    with ctrl2:
                        show_support_resistance = st.checkbox("Support/Resistance", value=st.session_state['chart_prefs']['sr'], key="chk_sr")
                        show_trade_setup = st.checkbox("Entry/Stop", value=st.session_state['chart_prefs']['ts'], key="chk_ts")
                    with ctrl3:
                        show_rsi = st.checkbox("Show RSI", value=st.session_state['chart_prefs']['rsi'], key="chk_rsi")
                        show_macd = st.checkbox("Show MACD", value=st.session_state['chart_prefs']['macd'], key="chk_macd")
                    with ctrl4:
                        show_bollinger = st.checkbox("Show BOLL", value=st.session_state['chart_prefs']['boll'], key="chk_boll")
                        
                        # HVN is synced to global database preferences
                        current_hvn = st.session_state.get('show_hvn', True)
                        show_hvn = st.checkbox("Show HVN", value=current_hvn, key="chk_hvn")
                        
                        if show_hvn != current_hvn:
                            with db.get_session() as session:
                                if AuthManager.update_hvn_preference(session, st.session_state['user_id'], show_hvn):
                                    st.session_state['show_hvn'] = show_hvn
                                    st.rerun()
                        
                        # Trend Channel toggle (only meaningful in Trend Trading)
                        if analysis.trading_style == "Trend Trading":
                            show_channel = st.checkbox(
                                "📉 Trend Channel",
                                value=st.session_state['chart_prefs'].get('channel', True),
                                key="chk_channel"
                            )
                        else:
                            show_channel = False

                    # Save local UI states back to prefs immediately
                    st.session_state['chart_prefs'].update({
                        'ema': show_ema,
                        'atr': show_atr,
                        'sr': show_support_resistance,
                        'ts': show_trade_setup,
                        'rsi': show_rsi,
                        'macd': show_macd,
                        'boll': show_bollinger,
                        'channel': show_channel
                    })
                    
                    # Get defaults for the current style
                    from src.trading_styles.factory import get_trading_style
                    style_strategy = get_trading_style(analysis.trading_style)
                    style_defaults = style_strategy.get_chart_defaults()
                    
                    # Generate unified interactive chart
                    chart_gen.generate_candlestick_chart(
                        analysis,
                        timeframe=st.session_state.get('timeframe', style_defaults.get('timeframe', 'W')),
                        default_range=st.session_state.get('zoom', style_defaults.get('zoom', '5Y')),
                        show_ema=show_ema,
                        show_atr=show_atr,
                        show_rsi=show_rsi,
                        show_macd=show_macd,
                        show_bollinger=show_bollinger,
                        show_support_resistance=show_support_resistance,
                        show_hvn=show_hvn,
                        show_trade_setup=show_trade_setup,
                        show_channel=show_channel,
                        height=800 if show_rsi or show_macd else 700
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
                    pass

            except Exception as e:
                st.error(f"UI Render Error: {e}")
                st.expander("Detailed Error Trace").write(e)
    
    elif not st.session_state.get('current_analysis'):
        st.info("👈 Enter a ticker symbol and click 'Analyze' to get started")


if __name__ == "__main__":
    main()
