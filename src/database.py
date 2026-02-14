"""Database connection and session management"""

import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base


class Database:
    """Database connection manager"""
    
    def __init__(self, db_path: str = "stock_analysis.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def init_db(self):
        """Create all tables if they don't exist"""
        Base.metadata.create_all(self.engine)
        print(f"Database initialized at: {self.db_path}")
        
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.
        
        Usage:
            with db.get_session() as session:
                # do work
                session.commit()
        """
        session = self.SessionLocal()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            
    def get_or_create_stock(self, session: Session, ticker: str, name: str = None, sector: str = None, industry: str = None):
        """
        Get existing stock or create new one.
        
        Args:
            session: Database session
            ticker: Stock ticker symbol
            name: Company name (optional)
            sector: Industry sector (optional)
            industry: Industry (optional)
            
        Returns:
            Stock object
        """
        from .models import Stock
        
        stock = session.query(Stock).filter(Stock.ticker == ticker).first()
        if not stock:
            stock = Stock(ticker=ticker, name=name, sector=sector)
            session.add(stock)
            session.flush()  # Get the ID without committing
        else:
            # Update if new info provided
            if name and not stock.name:
                stock.name = name
            if sector and not stock.sector:
                stock.sector = sector
        return stock

    def get_all_tickers(self) -> list[str]:
        """Get all unique tickers from the database"""
        from .models import Stock
        session = self.SessionLocal()
        try:
            tickers = session.query(Stock.ticker).filter(Stock.ticker != None).order_by(Stock.ticker).all()
            return [str(t[0]) for t in tickers if t[0]]
        except Exception as e:
            print(f"Error fetching tickers: {e}")
            return []
        finally:
            session.close()
