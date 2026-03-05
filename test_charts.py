import sys
import pandas as pd

try:
    from src.analyzer import StockAnalyzer
    from src.dashboard import chart_gen
except ImportError as e:
    print("ImportError:", e)
    sys.exit(1)

analyzer = StockAnalyzer()
analysis = analyzer.analyze("AAPL", trading_style="Swing Trading")

print("Got history:", len(analysis.history) if analysis.history is not None else 0)
print("Swing patterns:", len(getattr(analysis, 'swing_patterns', [])))
print("Trend:", getattr(analysis, 'market_trend', 'Unknown'))
print("Buy Score:", getattr(analysis, 'buy_score', 'N/A'))

print("\nTesting generate_candlestick_chart...")
try:
    chart_gen.generate_candlestick_chart(analysis)
    print("Chart generation didn't raise exceptions.")
except Exception as e:
    print("EXCEPTION IN CHART:", str(e))
