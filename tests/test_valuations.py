import pytest
import pandas as pd
from src.valuations import ValuationCalculator
from src.analyzer import StockAnalysis

def test_graham_number_calculation():
    """Test Graham Number formula: sqrt(22.5 * EPS * BookValue)"""
    analysis = StockAnalysis(ticker="TEST")
    analysis.basic_eps = 5.0
    analysis.book_value = 50.0
    
    # sqrt(22.5 * 5 * 50) = sqrt(5625) = 75.0
    result = ValuationCalculator.calculate_graham_number(analysis)
    assert result == pytest.approx(75.0)

def test_graham_number_invalid_data():
    """Test Graham Number with invalid/missing data"""
    analysis = StockAnalysis(ticker="TEST")
    
    # Missing data
    assert ValuationCalculator.calculate_graham_number(analysis) is None
    
    # Negative values (should return None or handle gracefully)
    analysis.basic_eps = -1.0
    analysis.book_value = 50.0
    assert ValuationCalculator.calculate_graham_number(analysis) is None

def test_dcf_basic_calculation():
    """Test DCF model with simple numbers"""
    analysis = StockAnalysis(ticker="TEST")
    analysis.free_cash_flow = 100.0
    analysis.shares_outstanding = 10
    analysis.total_debt = 50.0
    analysis.total_cash = 100.0
    analysis.earnings_growth = 0.05
    
    # Logic check:
    # FCF=100, Growth=5%, Discount=10%, Years=5
    # Y1: 105 / 1.1 = 95.45
    # Y2: 110.25 / 1.21 = 91.11
    # ... and so on
    result = ValuationCalculator.calculate_dcf(analysis, growth_rate=0.05, discount_rate=0.10)
    
    assert result is not None
    assert "intrinsic_value" in result
    assert result["intrinsic_value"] > 0
    assert result["growth_rate_used"] == 0.05

def test_dcf_shares_edge_case():
    """Test DCF with zero shares"""
    analysis = StockAnalysis(ticker="TEST")
    analysis.free_cash_flow = 100.0
    analysis.shares_outstanding = 0
    
    result = ValuationCalculator.calculate_dcf(analysis)
    assert result is None
