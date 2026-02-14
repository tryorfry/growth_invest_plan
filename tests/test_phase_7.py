import pytest
import asyncio
from src.data_sources.macro_source import MacroSource
from src.ai_analyst import AIAnalyst
from src.analyzer import StockAnalysis

@pytest.mark.asyncio
async def test_macro_source_fetch():
    """Test that MacroSource returns the expected keys"""
    data = await MacroSource.fetch_macro_data()
    assert '10Y_Yield' in data
    assert 'VIX' in data
    assert 'Yield_Spread' in data
    assert data['10Y_Yield']['value'] > 0

@pytest.mark.asyncio
async def test_sector_source_fetch():
    """Test that Sector data returns multiple sectors"""
    data = await MacroSource.fetch_sector_data()
    assert len(data) > 5
    assert 'Technology' in data

def test_ai_analyst_prompt_construction():
    """Test that AIAnalyst constructs a valid prompt string"""
    analysis = StockAnalysis(ticker="TSLA")
    analysis.current_price = 200.0
    analysis.rsi = 50.0
    analysis.atr = 5.0
    analysis.ema20 = 205.0
    analysis.ema50 = 210.0
    analysis.ema200 = 190.0
    analysis.macd = 1.0
    analysis.news_sentiment = 0.5
    analysis.news_summary = "Good news"
    
    analyst = AIAnalyst()
    prompt = analyst._construct_prompt(analysis)
    
    assert "TSLA" in prompt
    assert "Bull Case" in prompt
    assert "Final Verdict" in prompt
    assert "$200.00" in prompt
