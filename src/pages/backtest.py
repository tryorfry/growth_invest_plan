"""Backtesting page for strategy simulation"""

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from src.backtester import BacktestEngine

def render_backtesting_page():
    st.title("🧪 Strategy Backtester")
    st.markdown("Test technical strategies on historical data to see how they would have performed.")
    
    # Sidebar-like config in main area
    with st.sidebar:
        st.header("⚙️ Strategy Config")
        ticker = st.text_input("Ticker to Test", value="AAPL").upper()
        timeframe = st.selectbox("Historical Period", ["1y", "2y", "5y", "max"], index=0)
        strategy = st.selectbox("Select Strategy", ["EMA Crossover", "RSI Mean Reversion"])
        initial_capital = st.number_input("Initial Capital ($)", value=10000.0, step=1000.0)
        
        st.divider()
        if strategy == "EMA Crossover":
            short_ema = st.slider("Short EMA Period", 5, 50, 20)
            long_ema = st.slider("Long EMA Period", 20, 200, 50)
        else:
            oversold = st.slider("RSI Oversold (Buy)", 10, 40, 30)
            overbought = st.slider("RSI Overbought (Sell)", 60, 90, 70)
            
        run_button = st.button("🚀 Run Backtest", type="primary", use_container_width=True)

    if run_button and ticker:
        with st.spinner(f"Fetching {timeframe} history for {ticker}..."):
            t = yf.Ticker(ticker)
            df = t.history(period=timeframe)
            
        if df.empty:
            st.error(f"No data found for {ticker}")
            return

        # Run Simulation
        with st.spinner("Simulating strategy..."):
            if strategy == "EMA Crossover":
                results = BacktestEngine.run_ema_crossover(df, short_ema, long_ema, initial_capital)
            else:
                results = BacktestEngine.run_rsi_strategy(df, oversold, overbought, initial_capital)
        
        # Display Results
        st.subheader(f"📊 {strategy} Results for {ticker}")
        
        # Metrics Row
        cols = st.columns(len(results['metrics']))
        for i, (name, value) in enumerate(results['metrics'].items()):
            cols[i].metric(name, value)
            
        # Chart: Portfolio Value
        fig = go.Figure()
        
        # Comparison: Normalize Close price to initial capital for easy comparison
        normalized_close = (df['Close'] / df['Close'].iloc[0]) * initial_capital
        
        fig.add_trace(go.Scatter(
            x=results['data'].index,
            y=results['data']['portfolio_value'],
            name="Strategy Value",
            line=dict(color='green', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=normalized_close,
            name="Buy & Hold (Normalized)",
            line=dict(color='gray', width=1, dash='dot')
        ))
        
        fig.update_layout(
            title=f"Portfolio Value Over Time: {strategy}",
            xaxis_title="Date",
            yaxis_title="Value ($)",
            hovermode="x unified",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed Data
        with st.expander("👁️ View Full Simulation Data"):
            st.dataframe(results['data'])
    else:
        st.info("👈 Configure your strategy in the sidebar and click 'Run Backtest'")
