import pytest
from unittest.mock import patch, MagicMock
from src.ai_analyzer import AIAnalyzer

@pytest.fixture
def mock_stock_data():
    return {
        "current_price": 150.25,
        "trend": "Bullish",
        "support": 145.00,
        "resistance": 155.00,
        "sentiment": {"score": 0.8, "label": "Very Positive"},
        "hvn": 148.50,
        "earnings": {"drift_direction": "Up"}
    }

@patch('src.ai_analyzer.os.getenv')
def test_analyzer_unavailable_without_key(mock_getenv):
    """Test that analyzer gracefully degrades if no API key is found."""
    mock_getenv.return_value = None
    analyzer = AIAnalyzer()
    
    assert not analyzer.is_available()
    
    response = analyzer.generate_thesis("AAPL", {})
    assert "unavailable" in response.lower()
    assert "GEMINI_API_KEY" in response

@patch('src.ai_analyzer.os.getenv')
def test_prompt_construction(mock_getenv, mock_stock_data):
    """Test that the internal prompt builder correctly formats the stock dictionary."""
    mock_getenv.return_value = "fake_key"
    analyzer = AIAnalyzer()
    
    prompt = analyzer._construct_prompt("AAPL", mock_stock_data)
    
    assert "AAPL" in prompt
    assert "$150.25" in prompt
    assert "Bullish" in prompt
    assert "0.8" in prompt
    assert "$148.5" in prompt
    assert "Up" in prompt

@patch('src.ai_analyzer.genai.Client')
@patch('src.ai_analyzer.os.getenv')
def test_generate_thesis_success(mock_getenv, mock_client, mock_stock_data):
    """Test successful thesis generation using a mocked Gemini client."""
    mock_getenv.return_value = "fake_key"
    
    # Setup mock response chain: client.models.generate_content(...).text
    mock_response = MagicMock()
    mock_response.text = "AAPL shows strong bullish momentum holding above its $148 HVN."
    
    mock_models = MagicMock()
    mock_models.generate_content.return_value = mock_response
    
    mock_instance = MagicMock()
    mock_instance.models = mock_models
    mock_client.return_value = mock_instance
    
    analyzer = AIAnalyzer()
    
    # We must explicitly set this since the import try/catch in the module might 
    # flag HAS_GENAI = False if the test environment doesn't have it installed globally
    import src.ai_analyzer
    src.ai_analyzer.HAS_GENAI = True
    
    thesis = analyzer.generate_thesis("AAPL", mock_stock_data)
    
    assert "bullish momentum" in thesis
    mock_models.generate_content.assert_called_once()
