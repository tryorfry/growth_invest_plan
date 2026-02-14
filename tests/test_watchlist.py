"""Unit tests for watchlist management"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import Database
from src.watchlist import WatchlistManager
from src.models import Watchlist, WatchlistItem, Stock


@pytest.fixture
def db():
    """Create test database"""
    db = Database(":memory:")
    db.init_db()
    return db


@pytest.fixture
def wm(db):
    """Create watchlist manager"""
    with db.get_session() as session:
        yield WatchlistManager(session)


def test_create_watchlist(wm):
    """Test creating a watchlist"""
    watchlist = wm.create_watchlist("Tech Stocks", "Technology companies")
    
    assert watchlist is not None
    assert watchlist.name == "Tech Stocks"
    assert watchlist.description == "Technology companies"


def test_get_watchlist(wm):
    """Test retrieving a watchlist"""
    created = wm.create_watchlist("Test List")
    retrieved = wm.get_watchlist(created.id)
    
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.name == "Test List"


def test_get_all_watchlists(wm):
    """Test getting all watchlists"""
    wm.create_watchlist("List 1")
    wm.create_watchlist("List 2")
    wm.create_watchlist("List 3")
    
    all_lists = wm.get_all_watchlists()
    assert len(all_lists) >= 3


def test_add_stock_to_watchlist(wm):
    """Test adding a stock to watchlist"""
    watchlist = wm.create_watchlist("My List")
    item = wm.add_stock_to_watchlist(watchlist.id, "AAPL", "Apple Inc")
    
    assert item is not None
    assert item.watchlist_id == watchlist.id
    assert item.notes == "Apple Inc"


def test_add_duplicate_stock(wm):
    """Test adding same stock twice returns existing item"""
    watchlist = wm.create_watchlist("My List")
    
    item1 = wm.add_stock_to_watchlist(watchlist.id, "AAPL")
    item2 = wm.add_stock_to_watchlist(watchlist.id, "AAPL")
    
    assert item1.id == item2.id


def test_remove_stock_from_watchlist(wm):
    """Test removing a stock from watchlist"""
    watchlist = wm.create_watchlist("My List")
    wm.add_stock_to_watchlist(watchlist.id, "AAPL")
    
    result = wm.remove_stock_from_watchlist(watchlist.id, "AAPL")
    assert result is True
    
    stocks = wm.get_watchlist_stocks(watchlist.id)
    assert len(stocks) == 0


def test_get_watchlist_stocks(wm):
    """Test getting all stocks in a watchlist"""
    watchlist = wm.create_watchlist("Tech List")
    
    wm.add_stock_to_watchlist(watchlist.id, "AAPL", "Apple")
    wm.add_stock_to_watchlist(watchlist.id, "NVDA", "NVIDIA")
    wm.add_stock_to_watchlist(watchlist.id, "GOOGL", "Google")
    
    stocks = wm.get_watchlist_stocks(watchlist.id)
    
    assert len(stocks) == 3
    tickers = [s['ticker'] for s in stocks]
    assert "AAPL" in tickers
    assert "NVDA" in tickers
    assert "GOOGL" in tickers


def test_delete_watchlist(wm):
    """Test deleting a watchlist"""
    watchlist = wm.create_watchlist("Temp List")
    wm.add_stock_to_watchlist(watchlist.id, "AAPL")
    
    result = wm.delete_watchlist(watchlist.id)
    assert result is True
    
    retrieved = wm.get_watchlist(watchlist.id)
    assert retrieved is None


def test_get_default_watchlist(wm):
    """Test getting or creating default watchlist"""
    watchlist = wm.get_default_watchlist()
    
    assert watchlist is not None
    assert watchlist.name == "My Watchlist"
    
    # Should return same watchlist on second call
    watchlist2 = wm.get_default_watchlist()
    assert watchlist.id == watchlist2.id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
