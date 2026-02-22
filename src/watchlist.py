"""Watchlist management system"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models import Watchlist, WatchlistItem, Stock
from datetime import datetime


class WatchlistManager:
    """Manage stock watchlists"""
    
    def __init__(self, session: Session, user_id: int):
        self.session = session
        self.user_id = user_id
    
    def create_watchlist(self, name: str, description: str = "") -> Watchlist:
        """Create a new watchlist"""
        watchlist = Watchlist(
            name=name,
            description=description,
            user_id=self.user_id
        )
        self.session.add(watchlist)
        self.session.commit()
        return watchlist
    
    def get_watchlist(self, watchlist_id: int) -> Optional[Watchlist]:
        """Get watchlist by ID"""
        return self.session.query(Watchlist).filter(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == self.user_id
        ).first()
    
    def get_all_watchlists(self) -> List[Watchlist]:
        """Get all watchlists"""
        return self.session.query(Watchlist).filter(Watchlist.user_id == self.user_id).all()
    
    def add_stock_to_watchlist(self, watchlist_id: int, ticker: str, notes: str = "") -> Optional[WatchlistItem]:
        """Add a stock to a watchlist"""
        # Get or create stock
        stock = self.session.query(Stock).filter(Stock.ticker == ticker).first()
        if not stock:
            stock = Stock(ticker=ticker)
            self.session.add(stock)
            self.session.commit()
        
        # Check if already in watchlist
        existing = self.session.query(WatchlistItem).filter(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.stock_id == stock.id
        ).first()
        
        if existing:
            return existing
        
        # Add to watchlist
        item = WatchlistItem(
            watchlist_id=watchlist_id,
            stock_id=stock.id,
            notes=notes
        )
        self.session.add(item)
        self.session.commit()
        return item
    
    def remove_stock_from_watchlist(self, watchlist_id: int, ticker: str) -> bool:
        """Remove a stock from a watchlist"""
        stock = self.session.query(Stock).filter(Stock.ticker == ticker).first()
        if not stock:
            return False
        
        item = self.session.query(WatchlistItem).filter(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.stock_id == stock.id
        ).first()
        
        if item:
            self.session.delete(item)
            self.session.commit()
            return True
        return False
    
    def get_watchlist_stocks(self, watchlist_id: int) -> List[Dict[str, Any]]:
        """Get all stocks in a watchlist with their details"""
        watchlist = self.get_watchlist(watchlist_id)
        if not watchlist:
            return []
        
        stocks = []
        for item in watchlist.items:
            stocks.append({
                'ticker': item.stock.ticker,
                'name': item.stock.name,
                'sector': item.stock.sector,
                'notes': item.notes,
                'added_at': item.added_at
            })
        return stocks
    
    def delete_watchlist(self, watchlist_id: int) -> bool:
        """Delete a watchlist"""
        watchlist = self.get_watchlist(watchlist_id)
        if watchlist:
            self.session.delete(watchlist)
            self.session.commit()
            return True
        return False
    
    def get_default_watchlist(self) -> Watchlist:
        """Get or create the default watchlist"""
        watchlist = self.session.query(Watchlist).filter(
            Watchlist.name == "My Watchlist",
            Watchlist.user_id == self.user_id
        ).first()
        if not watchlist:
            watchlist = self.create_watchlist("My Watchlist", "Default watchlist")
        return watchlist
