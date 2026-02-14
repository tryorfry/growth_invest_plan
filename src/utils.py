
import streamlit as st
import pandas as pd
from datetime import datetime
from src.database import Database
from src.models import Stock, Analysis
from src.analyzer import StockAnalysis

def save_analysis(db: Database, analysis: StockAnalysis):
    """Shared logic to save analysis results to the database"""
    session = db.SessionLocal()
    try:
        # Get or create stock
        stock = db.get_or_create_stock(session, analysis.ticker)
        
        # Create analysis record
        analysis_record = Analysis(
            stock_id=stock.id,
            timestamp=analysis.timestamp,
            analysis_timestamp=analysis.analysis_timestamp,
            current_price=analysis.current_price,
            open_price=analysis.open,
            high=analysis.high,
            low=analysis.low,
            close=analysis.close,
            atr=analysis.atr,
            ema20=analysis.ema20,
            ema50=analysis.ema50,
            ema200=analysis.ema200,
            rsi=analysis.rsi,
            macd=analysis.macd,
            macd_signal=analysis.macd_signal,
            bollinger_upper=analysis.bollinger_upper,
            bollinger_lower=analysis.bollinger_lower,
            last_earnings_date=analysis.last_earnings_date,
            next_earnings_date=analysis.next_earnings_date,
            days_until_earnings=analysis.days_until_earnings,
            revenue=analysis.revenue,
            operating_income=analysis.operating_income,
            basic_eps=analysis.basic_eps,
            median_price_target=analysis.median_price_target,
            analyst_source=analysis.analyst_source,
            book_value=analysis.book_value,
            free_cash_flow=analysis.free_cash_flow,
            total_debt=analysis.total_debt,
            total_cash=analysis.total_cash,
            shares_outstanding=analysis.shares_outstanding,
            earnings_growth=analysis.earnings_growth,
            news_sentiment=analysis.news_sentiment,
            news_summary=analysis.news_summary
        )
        
        # Add Finviz data
        if analysis.finviz_data:
            analysis_record.market_cap = analysis.finviz_data.get("Market Cap")
            analysis_record.pe_ratio = _safe_float(analysis.finviz_data.get("P/E"))
            analysis_record.peg_ratio = _safe_float(analysis.finviz_data.get("PEG"))
            analysis_record.analyst_recom = _safe_float(analysis.finviz_data.get("Recom"))
            analysis_record.institutional_ownership = _safe_float(analysis.finviz_data.get("Inst Own", "").replace("%", ""))
            analysis_record.roe = _safe_float(analysis.finviz_data.get("ROE", "").replace("%", ""))
            analysis_record.roa = _safe_float(analysis.finviz_data.get("ROA", "").replace("%", ""))
            analysis_record.eps_growth_this_year = _safe_float(analysis.finviz_data.get("EPS this Y", "").replace("%", ""))
            analysis_record.eps_growth_next_year = _safe_float(analysis.finviz_data.get("EPS next Y", "").replace("%", ""))
        
        session.add(analysis_record)
        session.commit()
    finally:
        session.close()

def _safe_float(value):
    """Safely convert string to float"""
    try:
        if isinstance(value, (int, float)):
            return float(value)
        return float(value) if value and value != '-' else None
    except (ValueError, TypeError):
        return None

def render_ticker_header(analysis: StockAnalysis):
    """Render a consistent header for detailed analysis views"""
    st.markdown(f"## {analysis.company_name or analysis.ticker} ({analysis.ticker})")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        info_parts = []
        if analysis.sector:
            info_parts.append(f"**Sector:** {analysis.sector}")
        if analysis.industry:
            info_parts.append(f"**Industry:** {analysis.industry}")
        
        if info_parts:
            st.markdown(" | ".join(info_parts))
        
        # Dual Timestamps
        market_date = analysis.timestamp.strftime('%Y-%m-%d') if analysis.timestamp else "N/A"
        analysis_time = analysis.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S') if analysis.analysis_timestamp else "N/A"
        
        st.markdown(f"✅ **Market Data Date:** {market_date} | 🕒 **Analysis Performed:** {analysis_time}")
        st.caption("Market data reflects the last trading close. Analysis time is when the data was fetched.")
            
    with col2:
        st.markdown("**Quick Research Links:**")
        yfin_url = f"https://finance.yahoo.com/quote/{analysis.ticker}"
        finviz_url = f"https://finviz.com/quote.ashx?t={analysis.ticker}"
        st.markdown(f"[![YFinance](https://img.shields.io/badge/Yahoo-Finance-blue)]({yfin_url}) [![Finviz](https://img.shields.io/badge/Finviz-Data-orange)]({finviz_url})")
    
    st.divider()
