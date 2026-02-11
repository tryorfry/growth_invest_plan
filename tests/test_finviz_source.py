"""Unit tests for Finviz data source"""

import pytest
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from src.data_sources.finviz_source import FinvizSource


class TestFinvizSource:
    """Test suite for FinvizSource"""
    
    @pytest.fixture
    def finviz_source(self):
        """Create a FinvizSource instance for testing"""
        return FinvizSource()
    
    @pytest.fixture
    def mock_html_content(self):
        """Create mock HTML content similar to Finviz snapshot table"""
        html = """
        <html>
            <table class="snapshot-table2">
                <tr>
                    <td>Market Cap</td>
                    <td>3000.00B</td>
                    <td>P/E</td>
                    <td>25.50</td>
                </tr>
                <tr>
                    <td>ROE</td>
                    <td>35.70%</td>
                    <td>ROA</td>
                    <td>25.28%</td>
                </tr>
                <tr>
                    <td>EPS next 5Y</td>
                    <td>12.37%</td>
                    <td>PEG</td>
                    <td>1.89</td>
                </tr>
            </table>
        </html>
        """
        return html.encode('utf-8')
    
    def test_get_source_name(self, finviz_source):
        """Test that source name is correct"""
        assert finviz_source.get_source_name() == "Finviz"
    
    def test_parse_snapshot_table(self, finviz_source, mock_html_content):
        """Test parsing of Finviz snapshot table"""
        result = finviz_source._parse_snapshot_table(mock_html_content)
        
        assert isinstance(result, dict)
        assert result['Market Cap'] == '3000.00B'
        assert result['P/E'] == '25.50'
        assert result['ROE'] == '35.70%'
        assert result['EPS next 5Y'] == '12.37%'
    
    def test_parse_snapshot_table_missing_table(self, finviz_source):
        """Test parsing when snapshot table is missing"""
        html = b"<html><body>No table here</body></html>"
        result = finviz_source._parse_snapshot_table(html)
        
        assert result == {}
    
    def test_fetch_success(self, finviz_source, mock_html_content):
        """Test successful fetch operation"""
        with patch('curl_cffi.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = mock_html_content
            mock_get.return_value = mock_response
            
            result = finviz_source.fetch("AAPL")
            
            assert result is not None
            assert 'Market Cap' in result
            assert 'P/E' in result
    
    def test_fetch_http_error(self, finviz_source):
        """Test fetch with HTTP error"""
        with patch('curl_cffi.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response
            
            result = finviz_source.fetch("INVALID")
            
            assert result is None
    
    def test_fetch_network_exception(self, finviz_source):
        """Test fetch with network exception"""
        with patch('curl_cffi.requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            result = finviz_source.fetch("AAPL")
            
            assert result is None
    
    def test_url_construction(self, finviz_source):
        """Test that URL is constructed correctly"""
        with patch('curl_cffi.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b"<html></html>"
            mock_get.return_value = mock_response
            
            finviz_source.fetch("NVDA")
            
            # Verify the URL was called with correct ticker
            call_args = mock_get.call_args
            assert "NVDA" in call_args[0][0]
            assert "finviz.com" in call_args[0][0]
