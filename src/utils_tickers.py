import pandas as pd
import streamlit as st
import os

@st.cache_data(ttl=86400)
def get_sp500_tickers():
    """Fetches S&P 500 tickers from Wikipedia, caches them for 24h to avoid rate limits."""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        tables = pd.read_html(url)
        df = tables[0]
        # Clean up tickers (e.g. BRK.B -> BRK-B for Yahoo Finance)
        tickers = df['Symbol'].str.replace('.', '-', regex=False).tolist()
        return sorted(tickers)
    except Exception as e:
        # Fallback to top 20 if wiki fails
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "JPM", "JNJ", "V", "PG", "UNH", "MA", "HD", "CVX", "LLY", "ABBV", "BAC", "MRK"]

def render_hybrid_ticker_input(key_prefix=""):
    """
    Renders a hybrid ticker input:
    Returns the explicitly typed ticker if provided, otherwise the dropdown selection.
    """
    sp500 = get_sp500_tickers()
    
    col1, col2 = st.columns([1, 1])
    with col1:
        dropdown_val = st.selectbox(
            "Select Ticker (S&P 500)",
            options=[""] + sp500,
            index=0,
            key=f"{key_prefix}_dropdown",
            help="Choose from top 500 companies"
        )
    with col2:
        text_val = st.text_input(
            "Or Type Custom Ticker",
            value="",
            max_chars=10,
            key=f"{key_prefix}_text",
            help="Type ANY stock ticker (e.g., TSLA, PLTR)"
        ).upper()
        
    return text_val if text_val else dropdown_val
