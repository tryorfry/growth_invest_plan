import asyncio
import time
import sys
import os
import pandas as pd

# Add root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analyzer import StockAnalyzer

async def profile_analysis(ticker):
    analyzer = StockAnalyzer()
    print(f"\n🚀 PROFILING ANALYSIS FOR {ticker}...")
    
    start_total = time.time()
    
    # We will wrap the tasks to time them individually
    async def timed_task(name, coro):
        start = time.time()
        try:
            res = await coro
            end = time.time()
            print(f"  [TIME] {name:20} | {end - start:6.2f}s | Success")
            return res
        except Exception as e:
            end = time.time()
            print(f"  [TIME] {name:20} | {end - start:6.2f}s | FAILED: {e}")
            return None

    # Manually trigger the parallel block from _fetch_fresh_analysis logic
    print("📍 Phase 1: Parallel Fetch (Technical, Fundamental, News, Macro, Earnings)")
    p1_start = time.time()
    
    # Get last_earnings_date from technical (simplification for profiler)
    tech_data = await analyzer.technical_source.fetch(ticker)
    last_earnings = tech_data.get('last_earnings_date') if tech_data else None
    
    # These match src/analyzer.py:357
    tech_task = timed_task("Technical (yf)", analyzer.technical_source.fetch(ticker))
    fund_task = timed_task("Fundamental (finviz)", analyzer.fundamental_source.fetch(ticker))
    news_task = timed_task("News (sentiment)", analyzer.news_source.fetch(ticker))
    macro_task = timed_task("Macrotrends", analyzer.macrotrends_source.fetch(ticker))
    earnings_task = timed_task("Earnings (drift)", analyzer.earnings_source.fetch(ticker))
    analyst_task = timed_task("Analyst (MarketBeat)", analyzer.analyst_source.fetch(ticker, last_earnings_date=last_earnings))
    
    results = await asyncio.gather(tech_task, fund_task, news_task, macro_task, earnings_task, analyst_task)
    p1_end = time.time()
    print(f"📍 Phase 1 Complete in {p1_end - p1_start:.2f}s")
    
    print(f"\n🏁 Total Analysis Time: {time.time() - start_total:.2f}s")

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "TSLA"
    asyncio.run(profile_analysis(ticker))
