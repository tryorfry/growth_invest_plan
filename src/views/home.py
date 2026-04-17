import streamlit as st
import asyncio
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from typing import Optional

from src.analyzer import StockAnalyzer, StockAnalysis
from src.database import Database
from src.models import Stock, Analysis
from src.visualization_tv import TVChartGenerator
from src.utils import save_analysis, render_ticker_header
from src.components.checklist import render_checklist
from src.components.earnings import render_earnings_analysis_section

async def analyze_stock(ticker: str, analyzer: StockAnalyzer, trading_style: str = "Growth Investing", force_refresh: bool = False):
    """Analyze a stock ticker"""
    return await analyzer.analyze(ticker, trading_style_name=trading_style, verbose=False, force_refresh=force_refresh)

def load_historical_analyses(db: Database, ticker: str, limit: int = 30):
    """Load historical analyses for a ticker"""
    session = db.SessionLocal()
    try:
        stock = session.query(Stock).filter(Stock.ticker == ticker).first()
        if not stock: return None
        
        analyses = session.query(Analysis).filter(
            Analysis.stock_id == stock.id
        ).order_by(Analysis.timestamp.desc()).limit(limit).all()
        
        if not analyses: return None
        
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

def render_home_page(db: Database, analyzer: StockAnalyzer, chart_gen: TVChartGenerator, ticker: str, selected_style: str, analyze_button: bool):
    """
    Renders the primary Analysis (Home) page.
    """
    st.title(f"📊 {selected_style} Analyzer")
    st.markdown("Comprehensive stock analysis with technical indicators, fundamentals, and sentiment analysis")
    
    # 1. Trigger Analysis
    if analyze_button and ticker:
        with st.spinner(f"Analyzing {ticker}..."):
            try:
                fetched_analysis = asyncio.run(analyze_stock(ticker, analyzer, selected_style, force_refresh=True))
                
                if fetched_analysis:
                    save_analysis(db, fetched_analysis)
                    st.session_state['current_analysis'] = fetched_analysis
                    st.session_state['current_ticker'] = ticker
                    
                    # Alerts logic
                    try:
                        from src.alerts.alert_engine import AlertEngine
                        alert_engine = AlertEngine(use_email=False)
                        with db.get_session() as alert_session:
                            triggered = alert_engine.check_alerts(alert_session, fetched_analysis)
                            for t in triggered:
                                st.toast(f"🚨 **{ticker} Alert!** {t.get('alert_type', '').upper()} triggered.", icon="⚠️")
                    except: pass
                    
                    # Log activity
                    _uid = st.session_state.get('user_id')
                    if _uid:
                        from src.activity_logger import log_activity
                        log_activity(db, _uid, "Dashboard", f"analyze_{selected_style.lower().replace(' ', '_')}", ticker=ticker)
                else:
                    st.error(f"Failed to analyze {ticker}. Please check the ticker symbol.")
            except Exception as e:
                st.error(f"An error occurred: {e}")

    # 2. Render Results
    if st.session_state.get('current_analysis') and st.session_state.get('current_ticker') == ticker:
        try:
            analysis = st.session_state['current_analysis']
            render_ticker_header(analysis)
            
            if analysis.has_earnings_warning():
                st.warning(f"⚠️ **Earnings Alert:** Next earnings in {analysis.days_until_earnings} days ({analysis.next_earnings_date.date()})")
            
            # Metrics Rows
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Current Price", f"${analysis.current_price:.2f}")
            with col2:
                if analysis.median_price_target:
                    upside = ((analysis.median_price_target - analysis.current_price) / analysis.current_price) * 100
                    st.metric("Calculated MATP", f"${analysis.median_price_target:.2f}", f"{upside:+.1f}%")
                else: st.metric("Calculated MATP", "N/A")
            with col3: st.metric("RSI (14)", f"{analysis.rsi:.1f}")
            with col4:
                atr_val = analysis.atr_daily if analysis.trading_style in ["Swing Trading", "Trend Trading"] else analysis.atr
                st.metric(f"ATR (14{'d' if analysis.trading_style in ['Swing Trading', 'Trend Trading'] else 'w'})", f"{atr_val:.2f}")

            # Key Metrics Row 2: Earnings & Sentiment
            st.divider()
            col_e1, col_e2, col_e3, col_s = st.columns([1, 1, 2, 1])
            
            with col_e1:
                if analysis.last_earnings_date:
                    last_dt = pd.to_datetime(analysis.last_earnings_date).tz_localize(None).date()
                    days_since = (pd.Timestamp.now().normalize().date() - last_dt).days
                    st.metric("Last Earnings", str(last_dt), f"{days_since}d ago", delta_color="off")
                else:
                    st.metric("Last Earnings", "N/A")
                    
            with col_e2:
                if analysis.next_earnings_date:
                    next_dt = pd.to_datetime(analysis.next_earnings_date).tz_localize(None).date()
                    days_until = (next_dt - pd.Timestamp.now().normalize().date()).days
                    st.metric("Next Earnings", str(next_dt), f"in {days_until}d", delta_color="off")
                else:
                    st.metric("Next Earnings", "N/A")
                    
            with col_e3:
                if analysis.next_earnings_date:
                    next_dt = pd.to_datetime(analysis.next_earnings_date).tz_localize(None).date()
                    days_until = (next_dt - pd.Timestamp.now().normalize().date()).days
                    
                    if days_until <= 3: color, label = "#ef5350", "CRITICAL"
                    elif days_until <= 10: color, label = "#FF9800", "WARNING"
                    else: color, label = "#26a69a", "SAFE"
                    
                    st.markdown(f"""
                        <div style="display: flex; flex-direction: column; justify-content: center; height: 100%;">
                            <div style="font-size: 0.8rem; opacity: 0.8; margin-bottom: 4px;">Earnings Proximity</div>
                            <div style="background-color: {color}; height: 8px; border-radius: 4px; width: 100%;"></div>
                            <div style="font-size: 0.7rem; font-weight: bold; margin-top: 4px; color: {color};">{label}</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                     st.markdown('<div style="height: 60px; display: flex; align-items: center; opacity: 0.5;">No Earnings Data</div>', unsafe_allow_html=True)

            with col_s:
                if analysis.news_sentiment is not None:
                    label = "Bullish" if analysis.news_sentiment > 0.15 else "Bearish" if analysis.news_sentiment < -0.15 else "Neutral"
                    st.metric("Sentiment", label, f"{analysis.news_sentiment:.2f}")
                else:
                    st.metric("Sentiment", "N/A")

            # Sections
            if analysis.earnings_history and len(analysis.earnings_history) > 0:
                st.divider()
                render_earnings_analysis_section(analysis)
            
            if hasattr(analysis, 'market_trend') and analysis.market_trend:
                st.markdown(f"### Market Trend: :{'green' if analysis.market_trend == 'Uptrend' else 'red' if analysis.market_trend == 'Downtrend' else 'gray'}[{analysis.market_trend}]")

            if st.session_state.get('show_checklist', False) or (selected_style == "Growth Investing" and analysis.trading_style == "Growth Investing"):
                render_checklist(analysis)

            # AI Thesis
            st.divider()
            st.subheader("🤖 AI Investment Thesis")
            from src.ai_analyzer import AIAnalyzer
            with st.spinner("Generating AI Analysis..."):
                ai_engine = AIAnalyzer()
                if ai_engine.is_available():
                    ai_payload = {
                        "current_price": analysis.current_price, 
                        "trend": getattr(analysis, 'market_trend', 'Unknown'),
                        "sentiment": analysis.news_sentiment
                    }
                    st.info(ai_engine.generate_thesis(analysis.ticker, ai_payload))
                else:
                    st.warning("⚠️ AI Analysis unavailable.")

            # Trade Setup
            st.divider()
            st.subheader("🎯 Trade Execution Setup")
            with st.container(border=True):
                col_e, col_sl = st.columns(2)
                with col_e: st.metric("Suggested Entry", f"${float(analysis.suggested_entry):.2f}" if getattr(analysis, 'suggested_entry', None) is not None else "WAIT")
                with col_sl: st.metric("Stop Loss", f"${float(analysis.suggested_stop_loss):.2f}" if getattr(analysis, 'suggested_stop_loss', None) is not None else "N/A")
                
                if getattr(analysis, 'reward_to_risk', None):
                    st.divider()
                    col_rr, col_pt = st.columns(2)
                    with col_rr: st.metric("Reward/Risk", f"{analysis.reward_to_risk:.2f}x")
                    with col_pt: st.metric("Target Price", f"${float(analysis.target_price):.2f}" if getattr(analysis, 'target_price', None) else "N/A")

            # Chart
            st.subheader("📈 Technical Chart")
            prefs = st.session_state['chart_prefs']
            chart_gen.generate_candlestick_chart(
                analysis,
                timeframe=st.session_state.get('timeframe', 'D'),
                default_range=st.session_state.get('zoom', '1Y'),
                show_ema=prefs.get('ema', True),
                show_atr=prefs.get('atr', True),
                show_rsi=prefs.get('rsi', False),
                show_macd=prefs.get('macd', False),
                show_bollinger=prefs.get('boll', False),
                show_support_resistance=prefs.get('sr', True),
                show_hvn=st.session_state.get('show_hvn', True),
                show_trade_setup=prefs.get('ts', True)
            )

            # Fundamentals
            if analysis.finviz_data:
                st.subheader("💰 Fundamental Data")
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

            # Historical Chart
            st.subheader("📊 History")
            hist_df = load_historical_analyses(db, ticker)
            if hist_df is not None:
                st.line_chart(hist_df.set_index('Date')[['Price', 'RSI']])

        except Exception as e:
            st.error(f"Render Error: {e}")
    else:
        st.info("👈 Enter a ticker and click 'Analyze' to begin.")
