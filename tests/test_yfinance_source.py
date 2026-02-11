"""Unit tests for YFinance data source"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from datetime import datetime

from src.data_sources.yfinance_source import YFinanceSource


class TestYFinanceSource:
    """Test suite for YFinanceSource"""
    
    @pytest.fixture
    def yfinance_source(self):
        """Create a YFinanceSource instance for testing"""
        return YFinanceSource(period="2y")
    
    @pytest.fixture
    def mock_historical_data(self):
        """Create mock historical price data"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        data = {
            'Open': [100 + i for i in range(100)],
            'High': [105 + i for i in range(100)],
            'Low': [95 + i for i in range(100)],
            'Close': [100 + i for i in range(100)],
        }
        return pd.DataFrame(data, index=dates)
    
    def test_get_source_name(self, yfinance_source):
        """Test that source name is correct"""
        assert yfinance_source.get_source_name() == "YFinance"
    
    def test_fetch_returns_none_on_empty_history(self, yfinance_source):
        """Test that fetch returns None when no historical data is available"""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker.return_value.history.return_value = pd.DataFrame()
            result = yfinance_source.fetch("INVALID")
            assert result is None
    
    def test_calculate_technical_indicators(self, yfinance_source, mock_historical_data):
        """Test technical indicator calculations"""
        result = yfinance_source._calculate_technical_indicators(mock_historical_data)
        
        # Check that all expected keys are present
        expected_keys = [
            'atr', 'ema20', 'ema50', 'ema200',
            'open', 'high', 'low', 'close', 'current_price', 'timestamp'
        ]
        for key in expected_keys:
            assert key in result
        
        # Check that values are numeric (including numpy types)
        import numpy as np
        assert isinstance(result['atr'], (int, float, np.number))
        assert isinstance(result['ema20'], (int, float, np.number))
        assert isinstance(result['current_price'], (int, float, np.number))
    
    def test_get_earnings_dates_with_past_earnings(self, yfinance_source):
        """Test extraction of past earnings dates"""
        mock_ticker = Mock()
        
        # Create mock earnings dates
        dates = pd.DatetimeIndex([
            pd.Timestamp('2024-01-15', tz='UTC'),
            pd.Timestamp('2023-10-15', tz='UTC'),
        ])
        mock_earnings = pd.DataFrame({'EPS': [1.0, 0.9]}, index=dates)
        mock_ticker.earnings_dates = mock_earnings
        mock_ticker.calendar = None
        
        result = yfinance_source._get_earnings_dates(mock_ticker)
        
        assert 'last_earnings_date' in result
        assert result['last_earnings_date'] == dates[0]
    
    def test_get_earnings_dates_with_future_earnings(self, yfinance_source):
        """Test extraction of future earnings dates"""
        mock_ticker = Mock()
        
        # Create mock future earnings
        future_date = pd.Timestamp.now(tz='UTC') + pd.Timedelta(days=30)
        mock_ticker.calendar = {"Earnings Date": [future_date]}
        mock_ticker.earnings_dates = None
        
        result = yfinance_source._get_earnings_dates(mock_ticker)
        
        assert 'next_earnings_date' in result
        assert 'days_until_earnings' in result
        assert result['days_until_earnings'] > 0
    
    def test_get_financial_data(self, yfinance_source):
        """Test extraction of financial data"""
        mock_ticker = Mock()
        
        # Create mock quarterly financials
        financials = pd.DataFrame({
            'Q1 2024': {
                'Total Revenue': 1000000000,
                'Operating Income': 500000000,
                'Basic EPS': 2.5
            }
        })
        mock_ticker.quarterly_financials = financials
        
        result = yfinance_source._get_financial_data(mock_ticker)
        
        assert 'revenue' in result
        assert 'operating_income' in result
        assert 'basic_eps' in result
        assert result['revenue'] == 1000000000
    
    def test_fetch_integration(self, yfinance_source, mock_historical_data):
        """Integration test for complete fetch operation"""
        with patch('yfinance.Ticker') as mock_ticker_class:
            mock_ticker = Mock()
            mock_ticker.history.return_value = mock_historical_data
            mock_ticker.earnings_dates = None
            mock_ticker.calendar = None
            mock_ticker.quarterly_financials = pd.DataFrame()
            mock_ticker_class.return_value = mock_ticker
            
            result = yfinance_source.fetch("AAPL")
            
            assert result is not None
            assert 'atr' in result
            assert 'current_price' in result
