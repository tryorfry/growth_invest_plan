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
from src.visualization_plotly import PlotlyChartGenerator
from src.utils import save_analysis, render_ticker_header


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
    return db

# Initialize analyzer
@st.cache_resource
def init_analyzer():
    """Initialize stock analyzer"""
    return StockAnalyzer()

# Initialize chart generator
@st.cache_resource
def init_chart_generator():
    """Initialize Plotly chart generator"""
    return PlotlyChartGenerator()


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


def main():
    """Main dashboard application"""
    
    # Initialize resources
    db = init_database()
    chart_gen = init_chart_generator()
    
    # Store in session state
    if 'db' not in st.session_state:
        st.session_state['db'] = db
    
    # Sidebar navigation
    with st.sidebar:
        st.title("📊 Stock Analyzer")
        
        page = st.radio(
            "Navigation",
            options=[
                "🏠 Home",
                "🌍 Market Pulse",
                "💼 Portfolio",
                "🧪 Backtester",
                "📋 Watchlist",
                "🔔 Alerts",
                "🔬 Advanced Analytics",
                "📈 Comparison"
            ]
        )
        
        st.divider()
    
    # Route to pages
    if page == "🌍 Market Pulse":
        from src.pages.market_pulse import render_market_pulse_page
        render_market_pulse_page()
        return

    elif page == "💼 Portfolio":
        from src.pages.portfolio_tracker import render_portfolio_tracker_page
        render_portfolio_tracker_page()
        return

    elif page == "🧪 Backtester":
        from src.pages.backtest import render_backtesting_page
        render_backtesting_page()
        return

    elif page == "📋 Watchlist":
        from src.pages.watchlist import render_watchlist_page
        render_watchlist_page()
        return
    
    elif page == "🔔 Alerts":
        from src.pages.alerts import render_alerts_page
        render_alerts_page()
        return
    
    elif page == "🔬 Advanced Analytics":
        from src.pages.advanced_analytics import render_advanced_analytics_page
        render_advanced_analytics_page()
        return
    
    elif page == "📈 Comparison":
        from src.pages.comparison import render_comparison_page
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
            
        ticker = st.text_input("Stock Ticker", value=default_ticker, max_chars=10).upper()
        
        analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)
        
        st.divider()
        
        # Chart options
        st.subheader("Chart Options")
        show_ema = st.checkbox("Show EMAs", value=True)
        show_rsi = st.checkbox("Show RSI", value=True)
        show_macd = st.checkbox("Show MACD", value=True)
        show_bollinger = st.checkbox("Show Bollinger Bands", value=False)
        show_support_resistance = st.checkbox("Show Support/Resistance", value=True)
        show_trade_setup = st.checkbox("Show Trade Setup (Entry/Stop)", value=True)
        
        st.divider()
        st.divider()
        st.caption("Data sources: Yahoo Finance, Finviz, MarketBeat")
        
        st.divider()
        with st.expander("🔧 System"):
            if st.button("Clear Cache & Reload", type="secondary"):
                st.cache_resource.clear()
                st.rerun()
    
    # Main content
    if analyze_button and ticker:
        with st.spinner(f"Analyzing {ticker}..."):
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
                        if analysis.revenue:
                            revenue_b = analysis.revenue / 1e9
                            st.write(f"**Revenue (Q):** ${revenue_b:.2f}B")
                        else:
                            st.write("**Revenue (Q):** N/A")
                    
                    with col3:
                        if analysis.operating_income:
                            op_income_b = analysis.operating_income / 1e9
                            st.write(f"**Op Income (Q):** ${op_income_b:.2f}B")
                        else:
                            st.write("**Op Income (Q):** N/A")
                    
                    with col4:
                        if analysis.basic_eps:
                            st.write(f"**EPS (Q):** ${analysis.basic_eps:.2f}")
                        else:
                            st.write("**EPS (Q):** N/A")
                
                # Technical Indicators
                st.subheader("📈 Technical Indicators")
                
                # Generate interactive chart
                fig = chart_gen.generate_candlestick_chart(
                    analysis,
                    show_ema=show_ema,
                    show_bollinger=show_bollinger,
                    show_support_resistance=show_support_resistance,
                    show_trade_setup=show_trade_setup
                )
                st.plotly_chart(fig, width='stretch')
                
                # RSI Chart
                if show_rsi and analysis.history is not None:
                    fig_rsi = chart_gen.generate_rsi_chart(analysis)
                    st.plotly_chart(fig_rsi, width='stretch')
                
                # MACD Chart
                if show_macd and analysis.history is not None:
                    fig_macd = chart_gen.generate_macd_chart(analysis)
                    st.plotly_chart(fig_macd, width='stretch')
                
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
    
    else:
        st.info("👈 Enter a ticker symbol and click 'Analyze' to get started")


if __name__ == "__main__":
    main()
