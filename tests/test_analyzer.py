"""Unit tests for Stock Analyzer"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd

from src.analyzer import StockAnalyzer, StockAnalysis
from src.data_sources.base import DataSource


class MockDataSource(DataSource):
    """Mock data source for testing"""
    
    def __init__(self, data_to_return):
        self.data_to_return = data_to_return
    
    async def fetch(self, ticker: str, **kwargs):
        return self.data_to_return
    
    def get_source_name(self):
        return "MockSource"


class TestStockAnalysis:
    """Test suite for StockAnalysis dataclass"""
    
    def test_stock_analysis_initialization(self):
        """Test StockAnalysis can be initialized"""
        analysis = StockAnalysis(ticker="AAPL")
        assert analysis.ticker == "AAPL"
        assert analysis.current_price == 0.0
        assert analysis.finviz_data == {}
    
    def test_has_earnings_warning_true(self):
        """Test earnings warning when < 10 days"""
        analysis = StockAnalysis(ticker="AAPL", days_until_earnings=5)
        assert analysis.has_earnings_warning() is True
    
    def test_has_earnings_warning_false(self):
        """Test no earnings warning when >= 10 days"""
        analysis = StockAnalysis(ticker="AAPL", days_until_earnings=15)
        assert analysis.has_earnings_warning() is False
    
    def test_has_earnings_warning_none(self):
        """Test no earnings warning when days is None"""
        analysis = StockAnalysis(ticker="AAPL", days_until_earnings=None)
        assert analysis.has_earnings_warning() is False


class TestStockAnalyzer:
    """Test suite for StockAnalyzer"""
    
    @pytest.fixture
    def mock_technical_data(self):
        """Create mock technical data"""
        return {
            "current_price": 150.0,
            "open": 148.0,
            "high": 152.0,
            "low": 147.0,
            "close": 150.0,
            "atr": 5.0,
            "ema20": 145.0,
            "ema50": 140.0,
            "ema200": 130.0,
            "timestamp": pd.Timestamp("2024-01-15"),
            "last_earnings_date": pd.Timestamp("2024-01-10", tz='UTC'),
            "revenue": 1000000000,
            "operating_income": 500000000,
            "basic_eps": 2.5
        }
    
    @pytest.fixture
    def mock_fundamental_data(self):
        """Create mock fundamental data"""
        return {
            "Market Cap": "3000.00B",
            "P/E": "25.50",
            "ROE": "35.70%",
            "PEG": "1.89"
        }
    
    @pytest.fixture
    def mock_analyst_data(self):
        """Create mock analyst data"""
        return {
            "median_price_target": 200.0
        }
    
    @pytest.mark.asyncio
    async def test_analyzer_initialization_with_defaults(self):
        """Test that analyzer initializes with default sources"""
        analyzer = StockAnalyzer()
        assert analyzer.technical_source is not None
        assert analyzer.fundamental_source is not None
        assert analyzer.analyst_source is not None
    
    @pytest.mark.asyncio
    async def test_analyzer_initialization_with_custom_sources(self):
        """Test analyzer with custom data sources"""
        mock_tech = MockDataSource({})
        mock_fund = MockDataSource({})
        mock_analyst = MockDataSource({})
        
        analyzer = StockAnalyzer(
            technical_source=mock_tech,
            fundamental_source=mock_fund,
            analyst_source=mock_analyst
        )
        
        assert analyzer.technical_source == mock_tech
        assert analyzer.fundamental_source == mock_fund
        assert analyzer.analyst_source == mock_analyst
    
    @pytest.mark.asyncio
    async def test_analyze_returns_none_on_no_technical_data(self):
        """Test that analyze returns None when technical data fetch fails"""
        mock_tech = MockDataSource(None)
        analyzer = StockAnalyzer(technical_source=mock_tech)
        
        result = await analyzer.analyze("INVALID", verbose=False)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_analyze_success(self, mock_technical_data, mock_fundamental_data, mock_analyst_data):
        """Test successful analysis with all data sources"""
        mock_tech = MockDataSource(mock_technical_data)
        mock_fund = MockDataSource(mock_fundamental_data)
        mock_analyst = MockDataSource(mock_analyst_data)
        
        analyzer = StockAnalyzer(
            technical_source=mock_tech,
            fundamental_source=mock_fund,
            analyst_source=mock_analyst
        )
        
        result = await analyzer.analyze("AAPL", verbose=False)
        
        assert result is not None
        assert isinstance(result, StockAnalysis)
        assert result.ticker == "AAPL"
        assert result.current_price == 150.0
        assert result.atr == 5.0
        assert result.median_price_target == 200.0
        assert result.finviz_data == mock_fundamental_data
    
    def test_populate_technical_data(self, mock_technical_data):
        """Test that technical data is correctly populated"""
        analyzer = StockAnalyzer()
        analysis = StockAnalysis(ticker="AAPL")
        
        analyzer._populate_technical_data(analysis, mock_technical_data)
        
        assert analysis.current_price == 150.0
        assert analysis.atr == 5.0
        assert analysis.ema20 == 145.0
        assert analysis.revenue == 1000000000
    
    @pytest.mark.asyncio
    async def test_analyze_uppercase_ticker(self, mock_technical_data):
        """Test that ticker is converted to uppercase"""
        mock_tech = MockDataSource(mock_technical_data)
        analyzer = StockAnalyzer(technical_source=mock_tech)
        
        result = await analyzer.analyze("aapl", verbose=False)
        
        assert result.ticker == "AAPL"
    
    @pytest.mark.asyncio
    async def test_analyze_without_analyst_data_when_no_earnings(self):
        """Test that analyst data is not fetched when no earnings date"""
        tech_data = {"current_price": 150.0, "atr": 5.0}
        mock_tech = MockDataSource(tech_data)
        mock_analyst = Mock(spec=DataSource)
        mock_analyst.fetch = AsyncMock()  # Mock async fetch
        
        analyzer = StockAnalyzer(
            technical_source=mock_tech,
            analyst_source=mock_analyst
        )
        
        result = await analyzer.analyze("AAPL", verbose=False)
        
        # Analyst source should not be called
        mock_analyst.fetch.assert_not_called()
