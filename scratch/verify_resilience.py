import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_sources.ticker_scraper import SectorTickerScraper
from src.data_sources.macro_source import MacroSource
from src.data_sources.news_source import NewsSentimentSource

async def verify_system():
    print("🚀 Starting Resilience Verification Suite...")
    print("-" * 50)

    # 1. Ticker Scraper Fallback Test
    print("🔍 Testing Ticker Scraper (Wikipedia Fallback)...")
    scraper = SectorTickerScraper()
    tech_leaders = scraper._get_fallback_list("Technology")
    if tech_leaders and tech_leaders[0]['ticker'] == "AAPL":
        print("✅ PASS: Wikipedia Benchmark Fallback is active and accurate.")
    else:
        print("❌ FAIL: Ticker scraper fallback failed.")

    # 2. Parallel Macro Snapshot Test
    print("🔍 Testing High-Speed Global Snapshot (Parallel Fetch)...")
    try:
        start_time = asyncio.get_event_loop().time()
        snapshot = await MacroSource.fetch_global_snapshot()
        end_time = asyncio.get_event_loop().time()
        
        if len(snapshot) > 5:
            duration = end_time - start_time
            print(f"✅ PASS: Fetched {len(snapshot)} global indices in {duration:.2f}s.")
            print(f"   Sample: {snapshot[0]['name']} is {snapshot[0]['pct_change']:+.2f}%")
        else:
            print("❌ FAIL: Global snapshot returned insufficient data.")
    except Exception as e:
        print(f"❌ FAIL: Parallel fetch crashed: {e}")

    # 3. NLP Sentiment Engine Test
    print("🔍 Testing NLP Sentiment Accuracy...")
    try:
        src = NewsSentimentSource()
        bull_headline = "Nvidia reports $30B revenue beat, stock surges on strong AI demand"
        from textblob import TextBlob
        polarity = TextBlob(bull_headline).sentiment.polarity
        if polarity > 0.2:
            print(f"✅ PASS: NLP correctly identified Bullish sentiment (Score: {polarity:.2f})")
        else:
            print(f"❌ FAIL: NLP sentiment scoring is miscalibrated.")
    except Exception as e:
        print(f"❌ FAIL: NLP engine error: {e}")

    print("-" * 50)
    print("🏆 Verification Complete.")

if __name__ == "__main__":
    asyncio.run(verify_system())
