"""Unit tests for Risk Sizing and Position Calculation"""

import pytest
import pandas as pd
from unittest.mock import Mock, AsyncMock, patch
from src.analyzer import StockAnalyzer, StockAnalysis
from src.data_sources.base import DataSource

class MockDataSource(DataSource):
    def __init__(self, data):
        self.data = data
    async def fetch(self, ticker, **kwargs):
        return self.data
    def get_source_name(self):
        return "Mock"

@pytest.mark.asyncio
async def test_risk_sizing_logic_default():
    """Test that default NLV (10k) and Risk (1%) results in $100 cash risk"""
    mock_data = {
        "current_price": 100.0,
        "history": pd.DataFrame({"Close": [90, 95, 100], "High": [92, 97, 102], "Low": [88, 93, 98], "Open": [91, 96, 101]}, index=pd.date_range("2024-01-01", periods=3)),
        "atr": 5.0,
        "ema50": 90.0,
        "ema200": 80.0
    }
    
    analyzer = StockAnalyzer(technical_source=MockDataSource(mock_data))
    
    # Growth style typically sets entry near support and SL below support
    # We mock the analyzer to focus on the sizing calculation
    with patch('src.trading_styles.growth.GrowthStyle.calculate_trade_setup') as mock_setup:
        def side_effect(analysis):
            analysis.suggested_entry = 100.0
            analysis.suggested_stop_loss = 95.0 # $5 risk per unit
            analysis.target_price = 120.0
            
        mock_setup.side_effect = side_effect
        
        # NLV=10000, Risk=1% -> $100 risk. $100 / $5 = 20 units.
        result = await analyzer.analyze("AAPL", nlv=10000, risk_pct=1.0)
        
        assert result.risk_per_unit == 5.0
        assert result.position_size_units == 20

@pytest.mark.asyncio
async def test_risk_sizing_custom_nlv():
    """Test custom NLV and Risk percentage sizing"""
    mock_data = {
        "current_price": 100.0,
        "history": pd.DataFrame({"Close": [90, 95, 100]}, index=pd.date_range("2024-01-01", periods=3)),
        "atr": 5.0
    }
    
    analyzer = StockAnalyzer(technical_source=MockDataSource(mock_data))
    
    with patch('src.trading_styles.growth.GrowthStyle.calculate_trade_setup') as mock_setup:
        def side_effect(analysis):
            analysis.suggested_entry = 100.0
            analysis.suggested_stop_loss = 98.0 # $2 risk per unit
            analysis.target_price = 110.0
            
        mock_setup.side_effect = side_effect
        
        # NLV=50000, Risk=2% -> $1000 risk. $1000 / $2 = 500 units.
        result = await analyzer.analyze("AAPL", nlv=50000, risk_pct=2.0)
        
        assert result.risk_per_unit == 2.0
        assert result.position_size_units == 500

@pytest.mark.asyncio
async def test_multi_style_risk_sizing():
    """Test risk sizing in multi-style analysis"""
    mock_tech = {
        "history": pd.DataFrame({"Close": [100]*10}, index=pd.date_range("2024-01-01", periods=10)),
        "current_price": 100.0,
        "atr": 5.0,
        "atr_daily": 2.0
    }
    
    analyzer = StockAnalyzer(technical_source=MockDataSource(mock_tech))
    # Mocking other sources to avoid errors
    analyzer.fundamental_source = MockDataSource({})
    analyzer.news_source = MockDataSource({})
    analyzer.macrotrends_source = MockDataSource({})
    analyzer.earnings_source = MockDataSource({})
    analyzer.analyst_source = MockDataSource({})

    with patch('src.trading_styles.factory.get_trading_style') as mock_factory:
        mock_style = Mock()
        mock_style.style_name = "Growth Investing"
        mock_style.score_setup.return_value = 0.8
        
        def mock_calc(analysis):
            analysis.suggested_entry = 100.0
            analysis.suggested_stop_loss = 90.0 # $10 risk
            analysis.target_price = 130.0
        
        mock_style.calculate_trade_setup.side_effect = mock_calc
        mock_factory.return_value = mock_style
        
        # NLV=20000, Risk=1% -> $200 risk. $200 / $10 = 20 units.
        result = await analyzer.multi_analyze("AAPL", nlv=20000, risk_pct=1.0)
        
        # Check that the style result contains the correct sizing
        growth_res = result.style_results["Growth Investing"]
        assert growth_res["risk_pu"] == 10.0
        assert growth_res["units"] == 20
