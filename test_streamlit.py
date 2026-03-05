import sys
import streamlit as st
import traceback
from src.analyzer import StockAnalyzer
from src.dashboard import chart_gen
from src.trading_styles.factory import get_trading_style

analyzer = StockAnalyzer()
analysis = analyzer.analyze("AAPL", trading_style="Swing Trading")
try:
    print("Generating chart...", flush=True)
    chart_gen.generate_candlestick_chart(analysis)
    print("SUCCESS", flush=True)
except Exception as e:
    traceback.print_exc()
