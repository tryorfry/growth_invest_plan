import asyncio
import sys
import os
import json
from datetime import datetime

# Add root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_sources.earnings_source import EarningsSource
from src.analyzer import StockAnalyzer

async def debug_tsla():
    ticker = "TSLA"
    print(f"--- Debugging Earnings for {ticker} ---")
    
    # 1. Test EarningsSource directly
    src = EarningsSource()
    print(f"Fetching earnings drift for {ticker}...")
    drift_data = src.fetch_earnings_drift(ticker, limit=12)
    
    print(f"Drift Data Keys: {list(drift_data.keys())}")
    if "error" in drift_data:
        print(f"ERROR found in drift_data: {drift_data['error']}")
    
    print(f"Analyzed Events: {drift_data.get('analyzed_events')}")
    if drift_data.get('events'):
        print(f"Sample Event: {drift_data['events'][0]}")
    else:
        print("No events found.")

    # 2. Test full Analyzer
    print(f"\n--- Testing Full Analyzer for {ticker} ---")
    analyzer = StockAnalyzer()
    analysis = await analyzer.analyze(ticker, force_refresh=True)
    
    if analysis:
        print(f"Projected Gap Risk: {analysis.projected_gap_risk}")
        print(f"Earnings History Count: {len(analysis.earnings_history) if analysis.earnings_history else 0}")
    else:
        print("Analysis failed to return an object.")

if __name__ == "__main__":
    asyncio.run(debug_tsla())
