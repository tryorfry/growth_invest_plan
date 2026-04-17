import streamlit as st
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from src.auth import AuthManager
from src.theme_manager import ThemeManager

def render_sidebar(db) -> Tuple[str, str, bool, str]:
    """
    Renders the common sidebar for all dashboard pages.
    
    Returns:
        Tuple containing:
        - page (str): The currently selected navigation page
        - ticker (str): The currently entered ticker
        - analyze_button (bool): Whether the analyze button was clicked
        - selected_style (str): The currently selected trading style
    """
    with st.sidebar:
        st.title("📊 Stock Analyzer")
        
        # 1. User Info & Theme
        st.markdown(f"**Hello, {st.session_state.get('username', 'User')}!** 👋")
        
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
        
        # 2. Navigation
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
        
        if tier in ['premium', 'admin']:
            nav_options.extend(["🌍 Market Pulse", "🔬 Advanced Analytics"])
            
        if tier == 'admin':
            nav_options.extend(["🏁 Multi-Style", "🔍 Screener", "🛡️ Admin Dashboard"])

        if 'go_to_page' in st.session_state:
            target_page = st.session_state.pop('go_to_page')
            if target_page in nav_options:
                st.session_state['nav_radio'] = target_page
            
        page = st.radio("Navigation", options=nav_options, key="nav_radio")
        
        if tier == 'free':
            st.info("⭐ Upgrade to Premium to unlock the Market Pulse and Advanced Analytics!")
        
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            AuthManager.logout()
            
        # 3. Page-specific Settings (only show for Home or relevant pages)
        ticker = ""
        analyze_button = False
        selected_style = "Growth Investing"
        
        if page == "🏠 Home":
            from src import __version__
            st.caption(f"v{__version__}")
            
            st.header("⚙️ Settings")
            
            show_checklist = st.checkbox(
                "📋 Show Investment Checklist", 
                value=st.session_state.get('show_checklist', False),
                help="Show the fundamental growth checklist regardless of trading style."
            )
            st.session_state['show_checklist'] = show_checklist
            
            db_tickers = db.get_all_tickers()
            default_ticker = "AAPL"
            if db_tickers:
                selected_history = st.selectbox(
                    "Search History",
                    options=["Enter New..."] + db_tickers,
                    index=0
                )
                if selected_history != "Enter New...":
                    default_ticker = selected_history
            
            from src.utils_tickers import render_hybrid_ticker_input
            ticker = render_hybrid_ticker_input(key_prefix="main_dash")
            if not ticker: ticker = default_ticker
            
            st.divider()
            st.subheader("📈 Trading Strategy")
            
            can_swing = st.session_state.get('user_tier') in ('admin', 'premium') or st.session_state.get('can_use_swing_trading', False)
            can_trend = st.session_state.get('user_tier') in ('admin', 'premium')
            
            style_options = ["Growth Investing", "Swing Trading", "Trend Trading"]
            current_active_style = st.session_state.get('active_trading_style', "Growth Investing")
            default_index = style_options.index(current_active_style) if current_active_style in style_options else 0
            
            selected_style = st.selectbox(
                "Select Style",
                options=style_options,
                index=default_index
            )
            
            analyze_disabled = False
            if selected_style == "Swing Trading" and not can_swing:
                st.warning("🔒 Swing Trading is a premium feature.")
                analyze_disabled = True
            elif selected_style == "Trend Trading" and not can_trend:
                st.warning("🔒 Trend Trading is a premium feature.")
                analyze_disabled = True
            
            if not analyze_disabled:
                if st.session_state.get('active_trading_style') != selected_style:
                    from src.trading_styles.factory import get_trading_style
                    style_strategy = get_trading_style(selected_style)
                    defaults = style_strategy.get_chart_defaults()
                    st.session_state['chart_prefs'].update(defaults)
                    st.session_state['timeframe'] = defaults.get('timeframe', 'D')
                    st.session_state['zoom'] = defaults.get('zoom', '1Y')
                    st.session_state['active_trading_style'] = selected_style
                    if 'current_analysis' in st.session_state: del st.session_state['current_analysis']
            
            analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True, disabled=analyze_disabled)
            
            st.divider()
            st.subheader("⚖️ Position Sizing")
            st.session_state['acc_size'] = st.number_input("Account Size ($)", value=st.session_state.get('acc_size', 10000), step=1000)
            st.session_state['risk_pct'] = st.slider("Risk per Trade (%)", 0.25, 5.0, st.session_state.get('risk_pct', 1.0), 0.25)
            
            st.divider()
            with st.expander("🔧 System"):
                if st.button("Clear Cache & Reload"):
                    st.cache_resource.clear()
                    st.cache_data.clear()
                    st.rerun()
                    
        return page, ticker, analyze_button, selected_style
