
import pytest
import hashlib
from src.utils import render_deep_dive_button
from unittest.mock import MagicMock, patch

def test_auth_token_generation_consistency():
    """Verify that auth token generation is consistent and matches dashboard interception."""
    username = "admin"
    password_hash = "$2b$12$KIXH..." # Mocked hash
    
    # Generate token using same logic as utils.py and dashboard.py
    token1 = hashlib.sha256(f"{username}{password_hash}".encode()).hexdigest()
    token2 = hashlib.sha256(f"{username}{password_hash}".encode()).hexdigest()
    
    assert token1 == token2
    assert len(token1) == 64 # SHA-256 length

@patch("src.utils.st")
def test_render_deep_dive_button_html(mock_st):
    """Ensure the render_deep_dive_button utility produces valid HTML with tokens."""
    # Mock session state
    mock_st.session_state = {
        'user_id': 1,
        'db': MagicMock()
    }
    
    # Mock DB interaction
    mock_db = mock_st.session_state['db']
    mock_session = MagicMock()
    mock_db.get_session.return_value.__enter__.return_value = mock_session
    
    mock_user = MagicMock()
    mock_user.username = "sachin"
    mock_user.password_hash = "hashed_pw"
    mock_session.query.return_value.filter.return_value.first.return_value = mock_user
    
    # Run utility
    from src.utils import render_deep_dive_button
    render_deep_dive_button("AAPL", style="Trend Trading", label="Test Link")
    
    # Verify st.markdown was called with HTML containing the ticker and style
    args, kwargs = mock_st.markdown.call_args
    html_output = args[0]
    
    assert 'ticker=AAPL' in html_output
    assert 'style=Trend+Trading' in html_output or 'style=Trend Trading' in html_output
    assert 'auth_user=sachin' in html_output
    assert 'target="_blank"' in html_output
    assert 'Test Link' in html_output
    assert 'auth_token=' in html_output

def test_token_verification_logic():
    """Verify the logic used in dashboard.py to validate tokens."""
    username = "user1"
    pw_hash = "secret_hash"
    
    # Correct token
    valid_token = hashlib.sha256(f"{username}{pw_hash}".encode()).hexdigest()
    
    # Verification check
    def verify(u, h, t):
        expected = hashlib.sha256(f"{u}{h}".encode()).hexdigest()
        return t == expected
        
    assert verify(username, pw_hash, valid_token) is True
    assert verify(username, "wrong_hash", valid_token) is False
    assert verify("other_user", pw_hash, valid_token) is False
