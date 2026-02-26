"""Tests for StockAnalyzer resilience and fallback logic"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.analyzer import StockAnalyzer, StockAnalysis

@pytest.mark.asyncio
async def test_analyzer_macrotrends_fallback():
    # Mock data sources
    tech_source = AsyncMock()
    tech_source.fetch.return_value = {
        "current_price": 150.0,
        "revenue": 1000.0,  # YFinance revenue
        "operating_income": 200.0,
        "basic_eps": 5.0,
        "last_earnings_date": None
    }
    
    fund_source = AsyncMock()
    fund_source.fetch.return_value = {"P/E": "20"}
    
    news_source = AsyncMock()
    news_source.fetch.return_value = {}
    
    # 1. Macrotrends Success Scenario
    macro_source = AsyncMock()
    macro_source.fetch.return_value = {
        "revenue": 1200.0, # Macrotrends revenue (should override)
        "operating_income": 250.0,
        "eps_diluted": 6.0
    }
    
    analyzer = StockAnalyzer(
        technical_source=tech_source,
        fundamental_source=fund_source,
        news_source=news_source,
        macrotrends_source=macro_source
    )
    
    analysis = await analyzer.analyze("AAPL", verbose=False)
    
    assert analysis.revenue == 1200.0
    assert analysis.operating_income == 250.0
    assert analysis.basic_eps == 6.0

    # 2. Macrotrends Failure Scenario (Fallback)
    macro_source.fetch.return_value = None
    
    analysis = await analyzer.analyze("AAPL", verbose=False)
    
    # Should fall back to technical source data
    assert analysis.revenue == 1000.0
    assert analysis.operating_income == 200.0
    assert analysis.basic_eps == 5.0
