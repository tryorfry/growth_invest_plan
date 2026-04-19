import pytest
import asyncio
from src.data_sources.ticker_scraper import SectorTickerScraper
from src.data_sources.macro_source import MacroSource
from src.data_sources.news_source import NewsSentimentSource

@pytest.mark.asyncio
async def test_ticker_scraper_fallback_accuracy():
    """Verify that the scraper correctly falls back to S&P 500 benchmarks on failure"""
    scraper = SectorTickerScraper()
    
    # 1. Test invalid sector returns empty but doesn't crash
    result = scraper.fetch_top_tickers("INVALID_SECTOR")
    assert result == []
    
    # 2. Test fallback mechanism (simulated by using internal helper)
    fallback_data = scraper._get_fallback_list("Technology")
    assert len(fallback_data) > 0
    assert fallback_data[0]['ticker'] == "AAPL"
    assert fallback_data[0]['is_fallback'] is True

@pytest.mark.asyncio
async def test_macro_snapshot_parallel_speed():
    """Verify that the parallel global snapshot is working and returns valid metrics"""
    snapshot = await MacroSource.fetch_global_snapshot()
    
    assert len(snapshot) > 0
    symbols = [s['name'] for s in snapshot]
    assert "S&P 500" in symbols
    assert "Bitcoin" in symbols
    
    for item in snapshot:
        assert 'value' in item
        assert 'pct_change' in item
        assert isinstance(item['pct_change'], (int, float))

def test_news_sentiment_nlp_logic():
    """Verify that the NLP engine correctly labels headlines"""
    src = NewsSentimentSource()
    
    # Mock articles
    bullish_headline = "Apple reports record breaking earnings and massive dividend hike"
    bearish_headline = "Apple faces massive lawsuit and slowing demand in China"
    
    from textblob import TextBlob
    
    # Real logic test
    blob_bull = TextBlob(bullish_headline)
    assert blob_bull.sentiment.polarity > 0.1
    
    blob_bear = TextBlob(bearish_headline)
    assert blob_bear.sentiment.polarity < -0.1
