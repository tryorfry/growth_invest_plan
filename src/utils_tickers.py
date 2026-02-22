import pandas as pd
import streamlit as st
import os

@st.cache_data(ttl=86400)
def get_all_us_tickers():
    """Fetches all registered US tickers from the SEC, caches them for 24h to avoid rate limits."""
    try:
        import requests
        # The SEC requires a User-Agent header
        headers = {'User-Agent': 'GrowthInvestPlan/1.0 (contact@example.com)'}
        url = 'https://www.sec.gov/files/company_tickers.json'
        
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        
        # Format: {"0":{"cik_str":320193,"ticker":"AAPL","title":"Apple Inc."}, ...}
        tickers = [v['ticker'] for k, v in data.items()]
        # Remove empty strings and sort
        valid_tickers = [t.replace('.', '-') for t in tickers if t] # Yahoo finance uses '-'
        return sorted(list(set(valid_tickers)))
    except Exception as e:
        # Fallback to top 20 if SEC API fails
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "JPM", "JNJ", "V", "PG", "UNH", "MA", "HD", "CVX", "LLY", "ABBV", "BAC", "MRK"]

def render_hybrid_ticker_input(key_prefix=""):
    """
    Renders a hybrid ticker input:
    Returns the explicitly typed ticker if provided, otherwise the dropdown selection.
    """
    us_tickers = get_all_us_tickers()
    
    col1, col2 = st.columns([1, 1])
    with col1:
        dropdown_val = st.selectbox(
            "Select Ticker (US Equities)",
            options=[""] + us_tickers,
            index=0,
            key=f"{key_prefix}_dropdown",
            help="Choose from over 10,000+ registered US companies"
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
