import pytest
import os
import pandas as pd
from unittest.mock import patch, MagicMock

from src.services.export_service import export_reports_to_excel
from src.services.email_service import send_report_email

def test_export_reports_to_excel_success(tmp_path):
    reports = [
        {"Ticker": "AAPL", "Sector": "Technology", "Checklist Score": "8/9", "Growth Score": 75},
        {"Ticker": "MSFT", "Sector": "Technology", "Checklist Score": "7/9", "Growth Score": 80},
        {"Ticker": "JNJ", "Sector": "Healthcare", "Checklist Score": "6/9", "Growth Score": 60}
    ]
    
    # Use tmp_path to isolate test output
    output_dir = tmp_path / "reports"
    output_dir.mkdir()
    
    filepath = export_reports_to_excel(reports, output_dir=str(output_dir))
    
    assert os.path.exists(filepath)
    assert filepath.endswith(".xlsx")
    
    # Verify contents using pandas
    xls = pd.ExcelFile(filepath)
    assert "All Stocks" in xls.sheet_names
    assert "Technology" in xls.sheet_names
    assert "Healthcare" in xls.sheet_names
    
    df_all = pd.read_excel(filepath, sheet_name="All Stocks")
    assert len(df_all) == 3
    
    df_tech = pd.read_excel(filepath, sheet_name="Technology")
    assert len(df_tech) == 2

def test_export_reports_empty_list():
    with pytest.raises(ValueError):
        export_reports_to_excel([])

@patch('src.services.email_service.smtplib.SMTP_SSL')
@patch('src.services.email_service.os.getenv')
def test_send_report_email(mock_getenv, mock_smtp):
    # Mock environment variables
    def getenv_side_effect(key, default=None):
        if key == "SMTP_USER": return "test@example.com"
        if key == "SMTP_PASSWORD": return "secret"
        if key == "SMTP_HOST": return "smtp.gmail.com"
        if key == "SMTP_PORT": return "465"
        return default
        
    mock_getenv.side_effect = getenv_side_effect
    
    # Mock SMTP Server
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server
    
    result = send_report_email("dummy_path.xlsx", "recipient@example.com")
    
    assert result is True
    mock_server.login.assert_called_once_with("test@example.com", "secret")
    mock_server.send_message.assert_called_once()

# --- New Extensive Tests ---

@pytest.mark.asyncio
async def test_generate_reports_success():
    """Test the core report generation logic with a mocked analyzer."""
    from src.services.report_generator import generate_reports
    from src.analyzer import StockAnalysis
    from datetime import datetime
    
    # Setup mock analysis object
    mock_analysis = StockAnalysis(ticker="AAPL", analysis_timestamp=datetime.now())
    mock_analysis.current_price = 150.0
    mock_analysis.company_name = "Apple Inc."
    mock_analysis.sector = "Technology"
    mock_analysis.industry = "Consumer Electronics"
    mock_analysis.best_style = "Growth Investing"
    mock_analysis.reward_to_risk = 3.5
    mock_analysis.suggested_entry = 150.0
    mock_analysis.suggested_stop_loss = 140.0
    mock_analysis.target_price = 185.0
    mock_analysis.risk_per_unit = 10.0
    mock_analysis.position_size_units = 10
    mock_analysis.atr = 5.0
    mock_analysis.style_results = {
        "Growth Investing": {"score": 85, "trend": "Uptrend"}
    }
    mock_analysis.finviz_data = {
        "Inst Own": "60%",
        "Inst Trans": "1.2%",
        "Insider Own": "0.5%",
        "Insider Trans": "-0.1%"
    }
    
    with patch('src.services.report_generator.StockAnalyzer') as MockAnalyzer:
        mock_instance = MockAnalyzer.return_value
        # Mock multi_analyze to return our mock analysis
        async def mock_multi_analyze(ticker, **kwargs):
            return mock_analysis
        mock_instance.multi_analyze = mock_multi_analyze
        
        # Test generation for a single ticker
        reports = await generate_reports(["AAPL"])
        
        assert len(reports) == 1
        report = reports[0]
        
        # Assert formatting logic matches UI expectations
        assert report["Ticker"] == "AAPL"
        assert report["Company"] == "Apple Inc."
        assert report["Sector"] == "Technology"
        assert report["Current Price"] == 150.0
        assert report["Best Style"] == "Growth Investing"
        assert report["Growth Score"] == 85
        assert report["Inst Own"] == "60%"
        assert report["Position Size (Units)"] == 10
        assert "Checklist Score" in report
        assert "AI Conviction Summary" in report

@pytest.mark.asyncio
async def test_generate_reports_analyzer_failure():
    """Test graceful handling when analyzer returns None for a ticker."""
    from src.services.report_generator import generate_reports
    
    with patch('src.services.report_generator.StockAnalyzer') as MockAnalyzer:
        mock_instance = MockAnalyzer.return_value
        # Mock multi_analyze to fail
        async def mock_multi_analyze(ticker, **kwargs):
            return None
        mock_instance.multi_analyze = mock_multi_analyze
        
        reports = await generate_reports(["INVALID"])
        # Should gracefully return empty list, not crash
        assert len(reports) == 0

def test_automated_report_db_model():
    """Test that the SQLAlchemy model instantiation works with the new report_type."""
    from src.models import AutomatedReport
    import datetime
    
    # Create the object
    report = AutomatedReport(
        report_date=datetime.datetime.now(),
        report_type="Dynamic Reversal Screener",
        total_stocks_analyzed=10,
        report_data_json='[]'
    )
    
    assert report.report_type == "Dynamic Reversal Screener"
    assert report.total_stocks_analyzed == 10
