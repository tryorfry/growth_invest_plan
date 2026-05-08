"""Sector Rotation and Relative Strength Analysis View"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data_sources.sector_source import SectorSource
from src.activity_logger import log_page_visit

def render_sector_rotation_page():
    st.title("🔄 Sector Rotation & RS Analysis")
    st.markdown("""
        Find where the big money is moving. This page ranks the 11 S&P 500 sectors by their 
        **Weighted Relative Strength (RS)**. Growth investors focus on the top 2-3 sectors.
    """)
    
    # -- Activity tracking --
    _db = st.session_state.get('db')
    if _db:
        log_page_visit(_db, "SectorRotation")
        
    source = SectorSource()
    
    with st.spinner("Analyzing Sector Alpha..."):
        data = source.fetch_sector_performance()
        
    if not data:
        st.error("Failed to fetch sector data. Please check your internet connection.")
        return
        
    df = pd.DataFrame(data)
    
    # 1. Top Level Metrics (Top Sector)
    top_sector = df.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Leading Sector", top_sector['Sector'], f"{top_sector['RS Score']:.1f} RS")
    
    # Find biggest 1M gainer
    best_1m = df.sort_values('1M Return', ascending=False).iloc[0]
    col2.metric("Hot (1M)", best_1m['Sector'], f"{best_1m['1M Return']:+.1f}%")
    
    # Find biggest 1W gainer
    best_1w = df.sort_values('1W Return', ascending=False).iloc[0]
    col3.metric("Momentum (1W)", best_1w['Sector'], f"{best_1w['1W Return']:+.1f}%")
    
    # Relative to SPY
    col4.metric("Alpha vs SPY", f"{top_sector['Relative to SPY (1Y)']:+.1f}%")

    st.divider()
    
    # 2. RS Ranking Chart
    st.subheader("📊 Sector Relative Strength Ranking")
    
    # Color mapping based on RS Score
    df['Color'] = df['RS Score'].apply(lambda x: '#00C853' if x > 20 else ('#FFD600' if x > 0 else '#D50000'))
    
    fig = px.bar(
        df, 
        x='RS Score', 
        y='Sector', 
        orientation='h',
        color='Color',
        color_discrete_map='identity',
        text_auto='.1f',
        title="Weighted RS Score (3M 40%, 6M 30%, 1Y 30%)"
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # 3. Performance Matrix
    st.subheader("📈 Performance Matrix")
    
    # Format the dataframe for display
    display_df = df.copy()
    cols = ['Sector', 'Ticker', '1W Return', '1M Return', '3M Return', '6M Return', '1Y Return', 'RS Score']
    display_df = display_df[cols]
    
    def color_returns(val):
        color = '#00C853' if val > 0 else '#D50000'
        return f'color: {color}'

    styler = display_df.style.format({
        '1W Return': '{:+.2f}%',
        '1M Return': '{:+.2f}%',
        '3M Return': '{:+.2f}%',
        '6M Return': '{:+.2f}%',
        '1Y Return': '{:+.2f}%',
        'RS Score': '{:.1f}'
    })
    
    # Handle both old and new pandas versions (applymap deprecated in favor of map in 2.1.0)
    subset_cols = ['1W Return', '1M Return', '3M Return', '6M Return', '1Y Return']
    if hasattr(styler, 'map'):
        styler = styler.map(color_returns, subset=subset_cols)
    else:
        styler = styler.applymap(color_returns, subset=subset_cols)

    st.dataframe(
        styler,
        use_container_width=True,
        hide_index=True
    )
    
    # 4. Deep Dive Selection
    st.divider()
    st.subheader("🔍 Sector Deep-Dive")
    selected_sector_name = st.selectbox("Select a sector to see its top components:", df['Sector'].tolist())
    
    selected_ticker = df[df['Sector'] == selected_sector_name]['Ticker'].values[0]
    
    st.info(f"Scanning leading stocks in **{selected_sector_name} ({selected_ticker})**...")
    
    # Here we could list top stocks from that sector. 
    # For now, let's provide a quick list of 5 leaders (manual for now, could be dynamic later)
    leaders_map = {
        "Technology": ["NVDA", "MSFT", "AAPL", "AVGO", "ORCL"],
        "Healthcare": ["LLY", "UNH", "JNJ", "ABBV", "MRK"],
        "Financials": ["JPM", "V", "MA", "BAC", "WFC"],
        "Consumer Discretionary": ["AMZN", "TSLA", "HD", "MCD", "LOW"],
        "Communication Services": ["META", "GOOGL", "NFLX", "TMUS", "DIS"],
        "Industrials": ["GE", "CAT", "HON", "UNP", "BA"],
        "Consumer Staples": ["PG", "KO", "PEP", "COST", "WMT"],
        "Energy": ["XOM", "CVX", "COP", "SLB", "MPC"],
        "Utilities": ["NEE", "SO", "DUK", "CEG", "VST"],
        "Real Estate": ["PLD", "AMT", "EQIX", "WELL", "PSA"],
        "Materials": ["LIN", "APD", "SHW", "FCX", "NEM"]
    }
    
    sector_leaders = leaders_map.get(selected_sector_name, [])
    
    if sector_leaders:
        cols = st.columns(len(sector_leaders))
        for i, stock in enumerate(sector_leaders):
            if cols[i].button(stock, key=f"btn_{stock}"):
                st.session_state['main_dash_text'] = stock
                st.session_state['nav_radio'] = "🏠 Home"
                st.session_state['mp_deep_dive_trigger'] = True # Force auto-analyze
                st.rerun()
    
    st.caption("Click on a ticker above to jump to its deep-dive analysis.")
