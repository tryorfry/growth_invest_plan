import asyncio
import sys
import os
import pandas as pd
from datetime import datetime

# Add root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analyzer import StockAnalyzer

async def test_earnings_analysis():
    analyzer = StockAnalyzer()
    ticker = "NVDA" # NVDA usually has good earnings data
    print(f"Analyzing {ticker}...")
    
    analysis = await analyzer.analyze(ticker, trading_style_name="Growth Investing", verbose=True)
    
    if analysis:
        print(f"\nAnalysis for {analysis.ticker}:")
        print(f"Last Earnings: {analysis.last_earnings_date}")
        print(f"Next Earnings: {analysis.next_earnings_date}")
        print(f"Projected Gap Risk: {analysis.projected_gap_risk}%")
        
        print("\nHistorical Earnings History (Last 4):")
        if analysis.earnings_history:
            for event in analysis.earnings_history[:4]:
                print(f"Date: {event['date']}, T0 Reaction: {event['t0_return']:.2f}%")
        else:
            print("No earnings history found.")
    else:
        print("Analysis failed.")

if __name__ == "__main__":
    asyncio.run(test_earnings_analysis())
