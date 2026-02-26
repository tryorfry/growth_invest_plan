"""Unit tests for MacrotrendsSource"""

import pytest
from unittest.mock import MagicMock, patch
from src.data_sources.macrotrends_source import MacrotrendsSource

@pytest.fixture
def macrotrends_source():
    return MacrotrendsSource()

@pytest.mark.asyncio
async def test_macrotrends_source_name(macrotrends_source):
    assert macrotrends_source.get_source_name() == "Macrotrends"

@pytest.mark.asyncio
@patch("curl_cffi.requests.get")
async def test_macrotrends_fetch_success(mock_get, macrotrends_source):
    # Mock search/redirect response
    mock_search_response = MagicMock()
    mock_search_response.status_code = 200
    mock_search_response.url = "https://www.macrotrends.net/stocks/charts/AAPL/apple/revenue"
    
    # Mock metric response with JSON data
    mock_metric_response = MagicMock()
    mock_metric_response.status_code = 200
    mock_metric_response.text = 'var original_data = [{"field_name":"2023-09-30","v1":"383285.00000"}];'
    
    mock_get.side_effect = [mock_search_response, mock_metric_response, mock_metric_response, mock_metric_response]
    
    result = await macrotrends_source.fetch("AAPL")
    
    assert result is not None
    assert result["revenue"] == 383285.0
    assert result["operating_income"] == 383285.0
    assert result["eps_diluted"] == 383285.0

@pytest.mark.asyncio
@patch("curl_cffi.requests.get")
async def test_macrotrends_fetch_failure(mock_get, macrotrends_source):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response
    
    result = await macrotrends_source.fetch("INVALID")
    assert result is None
