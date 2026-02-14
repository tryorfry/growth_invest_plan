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
            db_path: Default path to SQLite database file if env var not set
        """
        # Prioritize environment variable for Cloud deployment (Supabase/Postgres)
        self.db_url = os.getenv("DATABASE_URL")
        
        if not self.db_url:
            self.db_url = f'sqlite:///{db_path}'
        
        # SQLAlchemy 1.4+ requires 'postgresql://' instead of 'postgres://'
        if self.db_url.startswith("postgres://"):
            self.db_url = self.db_url.replace("postgres://", "postgresql://", 1)
            
        self.engine = create_engine(self.db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def init_db(self):
        """Create all tables if they don't exist and handle schema updates"""
        Base.metadata.create_all(self.engine)
        
        # Schema migration logic
        from sqlalchemy import text, inspect
        inspector = inspect(self.engine)
        
        new_cols = [
            ("analyses", "analyst_source", "VARCHAR(50)"),
            ("analyses", "analysis_timestamp", "DATETIME"),
            ("analyses", "book_value", "FLOAT"),
            ("analyses", "free_cash_flow", "FLOAT"),
            ("analyses", "total_debt", "FLOAT"),
            ("analyses", "total_cash", "FLOAT"),
            ("analyses", "shares_outstanding", "INTEGER"),
            ("analyses", "earnings_growth", "FLOAT")
        ]
        
        # Check existing columns to avoid redundant ALTER TABLE calls
        existing_cols = {col['name'] for col in inspector.get_columns('analyses')}
        
        with self.engine.connect() as conn:
            for table, col, col_type in new_cols:
                if col not in existing_cols:
                    try:
                        # Normalize type for Postgres if needed (e.g., DATETIME -> TIMESTAMP)
                        sql_type = col_type
                        if "postgresql" in self.db_url and col_type == "DATETIME":
                            sql_type = "TIMESTAMP"
                            
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {sql_type}"))
                        conn.commit()
                        print(f"Added column {col} to {table}")
                    except Exception as e:
                        print(f"Error adding column {col}: {e}")
                    
        print(f"Database initialized at: {self.db_url.split('@')[-1] if '@' in self.db_url else self.db_url}")
        
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

    def get_all_portfolios(self) -> list:
        """Get all portfolios from the database"""
        from .models import Portfolio
        session = self.SessionLocal()
        try:
            return session.query(Portfolio).order_by(Portfolio.name).all()
        except Exception as e:
            print(f"Error fetching portfolios: {e}")
            return []
        finally:
            session.close()
