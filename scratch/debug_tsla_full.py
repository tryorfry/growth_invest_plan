import asyncio
import sys
import os
import pandas as pd
from datetime import datetime

# Add root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analyzer import StockAnalyzer

async def debug_analyzer():
    analyzer = StockAnalyzer()
    ticker = "TSLA"
    
    print(f"--- Triggering Full Analysis for {ticker} ---")
    analysis = await analyzer.analyze(ticker, force_refresh=True, verbose=True)
    
    print("\n--- Diagnostic Results ---")
    print(f"Ticker: {analysis.ticker}")
    print(f"Company: {analysis.company_name}")
    print(f"Current Price: {analysis.current_price}")
    
    print(f"\n[Earnings]")
    print(f"Last Earnings Date: {analysis.last_earnings_date}")
    print(f"Next Earnings Date: {analysis.next_earnings_date}")
    print(f"Days Until: {analysis.days_until_earnings}")
    print(f"Earnings History Events: {len(analysis.earnings_history) if analysis.earnings_history else 0}")
    print(f"Projected Gap Risk: {analysis.projected_gap_risk}")
    
    print(f"\n[Sentiment]")
    print(f"News Sentiment: {analysis.news_sentiment}")
    print(f"News Summary: {analysis.news_summary}")
    
    print(f"\n[Validation]")
    if analysis.last_earnings_date:
        print("✅ Last Earnings RECOVERED or FETCHED")
    else:
        print("❌ Last Earnings STILL MISSING")
        
    if analysis.news_sentiment is not None:
        print(f"✅ News Sentiment POPULATED ({analysis.news_sentiment})")
    else:
        print("❌ News Sentiment STILL NULL")
        
    if analysis.earnings_history:
        print(f"✅ Gap Risk Data AVAILABLE ({len(analysis.earnings_history)} events)")
    else:
        print("❌ Gap Risk Data MISSING")

if __name__ == "__main__":
    asyncio.run(debug_analyzer())
