import pytest
import pandas as pd
from unittest.mock import MagicMock
from src.portfolio_manager import PortfolioManager
from src.models import Portfolio, Transaction, Stock

@pytest.fixture
def mock_session():
    session = MagicMock()
    return session

@pytest.fixture
def portfolio_manager(mock_session):
    return PortfolioManager(mock_session, user_id=1)

def test_create_portfolio_with_initial_balance(portfolio_manager, mock_session):
    # Test creating a portfolio with an initial balance
    portfolio = portfolio_manager.create_portfolio("Test", "Test Desc", initial_balance=10000.0)
    
    # Check that initial balance is set correctly
    assert portfolio.initial_balance == 10000.0
    assert portfolio.name == "Test"
    mock_session.add.assert_called_once_with(portfolio)
    mock_session.commit.assert_called_once()

def test_get_portfolio_performance_empty(portfolio_manager, mock_session):
    # Setup mock portfolio with 10k balance
    mock_portfolio = MagicMock()
    mock_portfolio.id = 1
    mock_portfolio.initial_balance = 10000.0
    
    mock_session.query().filter().first.return_value = mock_portfolio
    mock_session.query().filter().all.return_value = [] # No transactions
    
    # Mock get_portfolio_holdings to return empty dataframe
    portfolio_manager.get_portfolio_holdings = MagicMock(return_value=pd.DataFrame())
    
    performance = portfolio_manager.get_portfolio_performance(1, {})
    
    assert performance['cash_balance'] == 10000.0
    assert performance['nlv'] == 10000.0
    assert performance['total_value'] == 0.0
    assert performance['total_cost'] == 0.0

def test_get_portfolio_performance_with_transactions(portfolio_manager, mock_session):
    # Setup mock portfolio with 10k balance
    mock_portfolio = MagicMock()
    mock_portfolio.id = 1
    mock_portfolio.initial_balance = 10000.0
    
    # Setup mock transactions
    t1 = MagicMock()
    t1.type = 'BUY'
    t1.quantity = 10
    t1.price = 150.0
    t1.fees = 5.0
    
    t2 = MagicMock()
    t2.type = 'SELL'
    t2.quantity = 5
    t2.price = 200.0
    t2.fees = 5.0
    
    # Cash should be: 10000.0 - (10*150 + 5) + (5*200 - 5)
    # = 10000.0 - 1505.0 + 995.0 = 9490.0
    
    mock_session.query().filter().first.return_value = mock_portfolio
    mock_session.query().filter().all.return_value = [t1, t2]
    
    # Mock holdings dataframe
    df_data = {
        'Ticker': ['AAPL'],
        'qty': [5],
        'total_spent': [750.0],
    }
    portfolio_manager.get_portfolio_holdings = MagicMock(return_value=pd.DataFrame(df_data))
    
    # Current price is 200
    current_prices = {'AAPL': 200.0}
    
    performance = portfolio_manager.get_portfolio_performance(1, current_prices)
    
    assert performance['cash_balance'] == 9490.0
    assert performance['total_value'] == 1000.0 # 5 shares * 200
    assert performance['total_cost'] == 750.0
    assert performance['nlv'] == 9490.0 + 1000.0 # cash + market value
    assert performance['total_pl'] == 250.0 # 1000 - 750
