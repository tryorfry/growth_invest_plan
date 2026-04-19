import asyncio
import sys
import os
import json
from datetime import datetime, timedelta

# Add root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analyzer import StockAnalyzer
from src.database import Database
from src.models import Analysis, Stock
from src.utils import save_analysis

async def test_modernization():
    analyzer = StockAnalyzer()
    db = Database("stock_analysis.db")
    db.init_db()
    
    ticker = "NVDA"
    print(f"--- Step 1: Fresh Analysis for {ticker} ---")
    analysis = await analyzer.analyze(ticker, trading_style_name="Growth Investing", verbose=True, force_refresh=True)
    
    if analysis:
        print(f"Fresh analysis performed. Gap Risk: {analysis.projected_gap_risk}%")
        # Save to DB
        save_analysis(db, analysis)
        print("Analysis saved to database.")
    
    print(f"\n--- Step 2: Cached Analysis for {ticker} ---")
    # This should hit the DB and NOT the external APIs
    cached_analysis = await analyzer.analyze(ticker, trading_style_name="Growth Investing", verbose=True)
    
    if cached_analysis:
        print(f"Cached analysis retrieved. Gap Risk: {cached_analysis.projected_gap_risk}%")
        print(f"Analysis Timestamp: {cached_analysis.analysis_timestamp}")
        
        if cached_analysis.earnings_history:
            print(f"Historical Earnings count: {len(cached_analysis.earnings_history)}")
        else:
            print("ERROR: earnings_history missing in cache.")
    else:
        print("ERROR: Cached analysis retrieval failed.")

if __name__ == "__main__":
    asyncio.run(test_modernization())
