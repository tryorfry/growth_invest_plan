"""Unit tests for Technical Analysis Logic (Phase 9 & 10)"""

import pytest
import pandas as pd
import numpy as np
from src.analyzer import StockAnalyzer, StockAnalysis

class TestTechnicalAnalysis:
    """Test suite for Technical Analysis features"""
    
    @pytest.fixture
    def mock_analysis(self):
        """Create a basic analysis object with mock history"""
        analysis = StockAnalysis(ticker="TEST")
        
        # Create 30 days of mock data
        dates = pd.date_range(end=pd.Timestamp.now(), periods=30)
        data = {
            'Open': [100.0] * 30,
            'High': [105.0] * 30,
            'Low': [95.0] * 30,
            'Close': [100.0] * 30,
            'Volume': [1000] * 30
        }
        analysis.history = pd.DataFrame(data, index=dates)
        analysis.current_price = 100.0
        analysis.atr = 2.0
        return analysis

    def test_smart_rounding(self):
        """Test the 'Beat the Crowd' rounding logic"""
        analyzer = StockAnalyzer()
        
        # Test various decimal inputs
        # Should round to nearest: .13, .17, .37, .43, .77, .83, .97
        
        # Case 1: Close to .13
        assert analyzer._apply_smart_rounding(10.10) == 10.13
        
        # Case 2: Close to .50 (should pick .43 or .57?) -> targets has .43
        assert analyzer._apply_smart_rounding(10.45) == 10.43
        
        # Case 3: Close to .77
        assert analyzer._apply_smart_rounding(10.75) == 10.77
        
        # Case 4: Close to .00 (next integer) -> .97 of previous or .13? 
        # The logic finds closest target in current integer.
        # 10.02 -> 10.13 (closest positive diff in list? All targets > 0)
        # 10.99 -> 10.97
        assert analyzer._apply_smart_rounding(10.99) == 10.97

    def test_trend_identification_uptrend(self, mock_analysis):
        """Test Uptrend detection"""
        # Setup: P > EMA50 > EMA200
        mock_analysis.current_price = 110.0
        mock_analysis.ema50 = 105.0
        mock_analysis.ema200 = 100.0
        
        analyzer = StockAnalyzer()
        analyzer._calculate_trade_setup(mock_analysis)
        
        assert mock_analysis.market_trend == "Uptrend"

    def test_trend_identification_downtrend(self, mock_analysis):
        """Test Downtrend detection"""
        # Setup: P < EMA50 < EMA200
        mock_analysis.current_price = 90.0
        mock_analysis.ema50 = 95.0
        mock_analysis.ema200 = 100.0
        
        analyzer = StockAnalyzer()
        analyzer._calculate_trade_setup(mock_analysis)
        
        assert mock_analysis.market_trend == "Downtrend"

    def test_trend_identification_sideways(self, mock_analysis):
        """Test Sideways detection"""
        # Setup: Mixed (e.g. Price < EMA50 but EMA50 > EMA200)
        mock_analysis.current_price = 102.0
        mock_analysis.ema50 = 105.0
        mock_analysis.ema200 = 100.0
        
        analyzer = StockAnalyzer()
        analyzer._calculate_trade_setup(mock_analysis)
        
        assert mock_analysis.market_trend == "Sideways"

    def test_support_resistance_calculation(self, mock_analysis):
        """Test local extrema detection"""
        # Create a specific pattern:
        # Day 10: Local Low at 90
        # Day 20: Local High at 110
        
        df = mock_analysis.history
        # Set a Local Low at index 10 (needs 2 days before/after higher)
        df.iloc[8:13, df.columns.get_loc('Low')] = [95, 92, 90, 93, 95] 
        
        # Set a Local High at index 20
        df.iloc[18:23, df.columns.get_loc('High')] = [105, 108, 110, 107, 105]
        
        analyzer = StockAnalyzer()
        
        # We need to set current price between them to detect both as relevant S/R
        mock_analysis.current_price = 100.0
        
        analyzer._calculate_support_resistance(mock_analysis)
        
        assert 90.0 in mock_analysis.support_levels
        assert 110.0 in mock_analysis.resistance_levels

    def test_trade_setup_generation(self, mock_analysis):
        """Test Entry and Stop Loss calculation"""
        analyzer = StockAnalyzer()
        
        # Setup: Current Price 105, Support at 100
        mock_analysis.current_price = 105.0
        mock_analysis.support_levels = [100.0]
        mock_analysis.atr = 2.0
        
        analyzer._calculate_trade_setup(mock_analysis)
        
        # Entry Logic: Support * 1.005 -> Smart Rounding
        # 100 * 1.005 = 100.50
        # Smart Rounding(100.50) -> Should be 100.43 (closest to .50 in our list [.37, .43, .77])?
        # Difference .43 is .07, difference .77 is .27. So 100.43.
        
        expected_entry = 100.43 # 100.5 rounded to nearest odd target
        
        assert mock_analysis.suggested_entry is not None
        # Allow small float diff
        assert abs(mock_analysis.suggested_entry - expected_entry) < 0.01
        
        # Stop Loss Logic: Support - ATR -> 100 - 2 = 98.0
        assert mock_analysis.suggested_stop_loss == 98.0
