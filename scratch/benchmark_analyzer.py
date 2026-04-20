
import asyncio
import time
import pandas as pd
from typing import Dict, Any
import sys
import os

# Set up path to import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analyzer import StockAnalyzer
from src.data_sources.news_source import NewsSentimentSource
from src.data_sources.finviz_source import FinvizSource
from src.data_sources.macrotrends_source import MacrotrendsSource
from src.data_sources.yfinance_source import YFinanceSource
from src.data_sources.earnings_source import EarningsSource

async def benchmark_source(name: str, coro):
    start = time.time()
    try:
        result = await coro
        end = time.time()
        print(f"  [BENCH] {name:20} | Time: {end - start:6.2f}s | Success: {result is not None}")
        return end - start
    except Exception as e:
        end = time.time()
        print(f"  [BENCH] {name:20} | Time: {end - start:6.2f}s | ERROR: {e}")
        return end - start

async def run_detailed_benchmarks(ticker: str = "TSLA"):
    print(f"\n🚀 Starting Deep Benchmarks for {ticker}...")
    print("-" * 60)
    
    analyzer = StockAnalyzer()
    
    # 1. Individual Source Speed
    sources = [
        ("Daily Technicals", YFinanceSource().fetch(ticker, interval="1d", period="2y")),
        ("Weekly Technicals", YFinanceSource().fetch(ticker, interval="1wk", period="5y")),
        ("Finviz Fundamental", FinvizSource().fetch(ticker)),
        ("News Sentiment", NewsSentimentSource().fetch(ticker)),
        ("Macrotrends Core", MacrotrendsSource().fetch(ticker)),
        ("Earnings Gaps", EarningsSource().fetch(ticker)),
    ]
    
    results = {}
    print("\n📍 Individual Component Latency (Parallel):")
    tasks = [benchmark_source(name, coro) for name, coro in sources]
    times = await asyncio.gather(*tasks)
    
    # 2. Sequential Analysis (The worst-case scenario)
    print("\n📍 Sequential Baseline (Single-Threaded Simulation):")
    total_sequential = 0
    # Re-running news specifically to see if caching helps or if initialization is slow
    print("  (Repeating News to check caching impact...)")
    news_start = time.time()
    await NewsSentimentSource().fetch(ticker)
    news_end = time.time()
    print(f"  [BENCH] News (Cached)       | Time: {news_end - news_start:6.2f}s")
    
    # 3. Overall multi_analyze
    print("\n📍 Overall multi_analyze pipeline:")
    start = time.time()
    await analyzer.multi_analyze(ticker, verbose=False)
    end = time.time()
    print(f"  [BENCH] Total Pipeline      | Time: {end - start:6.2f}s")
    print("-" * 60)

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "TSLA"
    asyncio.run(run_detailed_benchmarks(ticker))
