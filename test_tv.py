import streamlit as st
from src.visualization_tv import TVChartGenerator
from src.analyzer import StockAnalysis
import pandas as pd

st.title("Test TV Chart")

# Create dummy data
a = StockAnalysis('AAPL')
a.history = pd.DataFrame({'Open': [150, 152, 151], 'High': [155, 153, 154], 'Low': [149, 150, 148], 'Close': [152, 151, 153], 'Volume': [1000, 1200, 900]}, index=pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03']))
a.suggested_entry = 155
a.suggested_stop_loss = 148

gen = TVChartGenerator()
gen.generate_candlestick_chart(a)
