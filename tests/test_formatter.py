"""Unit tests for AnalysisFormatter"""

import pytest
from unittest.mock import patch
import pandas as pd
from io import StringIO

from src.analyzer import StockAnalysis
from src.formatter import AnalysisFormatter


class TestAnalysisFormatter:
    """Test suite for AnalysisFormatter"""
    
    def test_format_number_with_value(self):
        """Test number formatting with valid value"""
        result = AnalysisFormatter.format_number(123.456, decimals=2)
        assert result == "123.46"
    
    def test_format_number_with_none(self):
        """Test number formatting with None"""
        result = AnalysisFormatter.format_number(None)
        assert result == "N/A"
    
    def test_format_number_custom_decimals(self):
        """Test number formatting with custom decimal places"""
        result = AnalysisFormatter.format_number(123.456789, decimals=4)
        assert result == "123.4568"
    
    def test_format_currency_billions(self):
        """Test currency formatting for billions"""
        result = AnalysisFormatter.format_currency(3000000000)
        assert result == "$3.00B"
    
    def test_format_currency_millions(self):
        """Test currency formatting for millions"""
        result = AnalysisFormatter.format_currency(5000000)
        assert result == "$5.00M"
    
    def test_format_currency_thousands(self):
        """Test currency formatting for thousands"""
        result = AnalysisFormatter.format_currency(50000)
        assert result == "$50,000.00"
    
    def test_format_currency_none(self):
        """Test currency formatting with None"""
        result = AnalysisFormatter.format_currency(None)
        assert result == "N/A"
    
    def test_format_currency_invalid_type(self):
        """Test currency formatting with invalid type"""
        result = AnalysisFormatter.format_currency("invalid")
        assert result == "N/A"
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_analysis_basic(self, mock_stdout):
        """Test basic analysis printing"""
        analysis = StockAnalysis(
            ticker="AAPL",
            current_price=150.0,
            open=148.0,
            high=152.0,
            low=147.0,
            close=150.0,
            atr=5.0,
            ema20=145.0,
            ema50=140.0,
            ema200=130.0,
            timestamp=pd.Timestamp("2024-01-15")
        )
        
        AnalysisFormatter.print_analysis(analysis)
        output = mock_stdout.getvalue()
        
        assert "AAPL" in output
        assert "150.00" in output
        assert "ATR (14)" in output
        assert "EMA 20" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_analysis_with_earnings_warning(self, mock_stdout):
        """Test printing with earnings warning"""
        analysis = StockAnalysis(
            ticker="NVDA",
            current_price=200.0,
            atr=10.0,
            ema20=190.0,
            ema50=180.0,
            ema200=170.0,
            next_earnings_date=pd.Timestamp("2024-02-01"),
            days_until_earnings=5,
            timestamp=pd.Timestamp("2024-01-15"),
            revenue=1000000000  # Add financial data so section prints
        )
        
        AnalysisFormatter.print_analysis(analysis)
        output = mock_stdout.getvalue()
        
        assert "WARNING" in output
        assert "5 days left" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_analysis_with_finviz_data(self, mock_stdout):
        """Test printing with Finviz data"""
        analysis = StockAnalysis(
            ticker="GOOGL",
            current_price=100.0,
            atr=3.0,
            ema20=95.0,
            ema50=90.0,
            ema200=85.0,
            timestamp=pd.Timestamp("2024-01-15"),
            finviz_data={
                "Market Cap": "3000.00B",
                "P/E": "25.50",
                "ROE": "35.70%",
                "PEG": "1.89"
            }
        )
        
        AnalysisFormatter.print_analysis(analysis)
        output = mock_stdout.getvalue()
        
        assert "Finviz Data" in output
        assert "3000.00B" in output
        assert "25.50" in output
    
    @patch('sys.stdout', new_callable=StringIO)
    def test_print_analysis_with_financials(self, mock_stdout):
        """Test printing with financial data"""
        analysis = StockAnalysis(
            ticker="MSFT",
            current_price=300.0,
            atr=8.0,
            ema20=290.0,
            ema50=280.0,
            ema200=270.0,
            timestamp=pd.Timestamp("2024-01-15"),
            revenue=50000000000,
            operating_income=20000000000,
            basic_eps=3.5
        )
        
        AnalysisFormatter.print_analysis(analysis)
        output = mock_stdout.getvalue()
        
        assert "Fundamentals" in output
        assert "$50.00B" in output
        assert "$20.00B" in output
        assert "3.50" in output
