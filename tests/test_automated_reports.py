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
