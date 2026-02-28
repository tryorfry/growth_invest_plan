"""Backtesting page for strategy simulation"""

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.backtester import BacktestEngine

def render_backtesting_page():
    st.title("🧪 Advanced Walk-Forward Backtester")
    st.markdown("Test technical strategies on historical data with institutional-grade metrics.")
    
    # Sidebar-like config in main area
    with st.sidebar:
        st.header("⚙️ Strategy Config")
        ticker = st.text_input("Ticker to Test", value="AAPL").upper()
        timeframe = st.selectbox("Historical Period", ["1y", "2y", "5y", "max"], index=1)
        strategy = st.selectbox("Select Strategy", ["Combined Alpha (EMA+RSI)", "EMA Crossover", "RSI Mean Reversion"])
        initial_capital = st.number_input("Initial Capital ($)", value=10000.0, step=1000.0)
        
        st.divider()
        if strategy == "EMA Crossover":
            short_ema = st.slider("Short EMA Period", 5, 50, 20)
            long_ema = st.slider("Long EMA Period", 20, 200, 50)
        elif strategy == "RSI Mean Reversion":
            oversold = st.slider("RSI Oversold (Buy)", 10, 40, 30)
            overbought = st.slider("RSI Overbought (Sell)", 60, 90, 70)
        else:
            st.info("Combined Alpha buys on oversold pullbacks (RSI < 45) during an uptrend (EMA20 > EMA50).")
            
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
            elif strategy == "RSI Mean Reversion":
                results = BacktestEngine.run_rsi_strategy(df, oversold, overbought, initial_capital)
            else:
                results = BacktestEngine.run_combined_strategy(df, initial_capital)
        
        # Display Results
        st.subheader(f"📊 {strategy} Results for {ticker}")
        
        # Metrics Row 1
        cols1 = st.columns(4)
        cols1[0].metric("Final Value", results['metrics']['Final Value'], results['metrics']['Total Return'])
        cols1[1].metric("Net Profit", results['metrics']['Net Profit'])
        cols1[2].metric("Buy & Hold Return", results['metrics']['Buy & Hold Return'])
        cols1[3].metric("Max Drawdown", results['metrics']['Max Drawdown'], delta_color="inverse")
        
        st.write("")
        
        # Metrics Row 2
        cols2 = st.columns(4)
        cols2[0].metric("Win Rate", results['metrics']['Win Rate'])
        cols2[1].metric("Profit Factor", results['metrics']['Profit Factor'])
        total_trades = len([t for t in results['trades'] if t['type'] == 'sell'])
        cols2[2].metric("Total Closed Trades", total_trades)
        
        # Chart: Portfolio Value & Drawdown
        normalized_close = (df['Close'] / df['Close'].iloc[0]) * initial_capital
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.05, row_heights=[0.7, 0.3])
        
        # Top chart - Equity Curve
        fig.add_trace(go.Scatter(
            x=results['data'].index, y=results['data']['portfolio_value'],
            name="Strategy Value", fill='tozeroy', line=dict(color='green', width=2)
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=df.index, y=normalized_close,
            name="Buy & Hold (Normalized)", line=dict(color='gray', width=1, dash='dot')
        ), row=1, col=1)
        
        # Bottom chart - Drawdown
        fig.add_trace(go.Scatter(
            x=results['data'].index, y=results['data']['drawdown'],
            name="Drawdown %", fill='tozeroy', line=dict(color='red', width=1)
        ), row=2, col=1)
        
        fig.update_layout(
            title=f"Equity Curve & Drawdown: {strategy}",
            hovermode="x unified",
            height=700,
            showlegend=True,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        # Fix y-axis titles
        fig.update_yaxes(title_text="Portfolio Value ($)", row=1, col=1)
        fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Trade Log
        with st.expander("📝 View Trade Log"):
            if results['trades']:
                trade_df = pd.DataFrame(results['trades'])
                # Format dates
                trade_df['date'] = trade_df['date'].dt.strftime('%Y-%m-%d %H:%M')
                st.dataframe(trade_df, use_container_width=True)
            else:
                st.info("No trades executed.")
                
        # Detailed Data
        with st.expander("👁️ View Full Simulation Data"):
            st.dataframe(results['data'])
    else:
        st.info("👈 Configure your strategy in the sidebar and click 'Run Backtest'")
