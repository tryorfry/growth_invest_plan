"""Database connection and session management"""

import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
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
        
        # Get from Streamlit Secrets natively first, fallback to os env
        # This completely bypasses environment variable caching issues
        try:
            import streamlit as st
            if "DATABASE_URL" in st.secrets:
                self.db_url = st.secrets["DATABASE_URL"]
        except Exception:
            pass

        if not self.db_url:
            self.db_url = f'sqlite:///{db_path}'
        
        # SQLAlchemy 1.4+ requires 'postgresql://' instead of 'postgres://'
        if self.db_url.startswith("postgres://"):
            self.db_url = self.db_url.replace("postgres://", "postgresql://", 1)

        # Adding connect_args to prevent connection timeouts on Supabase pooled connections
        connect_args = {}
        is_postgres = False
        if isinstance(self.db_url, str):
            is_postgres = self.db_url.startswith("postgresql")
        else:
            # Handle SQLAlchemy URL object
            is_postgres = getattr(self.db_url, "drivername", "").startswith("postgresql")

        if is_postgres:
            connect_args = {
                "keepalives": 1, 
                "keepalives_idle": 30, 
                "keepalives_interval": 10, 
                "keepalives_count": 5,
                "sslmode": "require"
            }
            self.engine = create_engine(self.db_url, echo=False, connect_args=connect_args, poolclass=NullPool)
        else:
            self.engine = create_engine(self.db_url, echo=False, connect_args=connect_args)
            
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def init_db(self):
        """Create all tables if they don't exist and handle schema updates"""
        Base.metadata.create_all(self.engine)
        
        # Schema migration logic
        from sqlalchemy import text, inspect
        inspector = inspect(self.engine)
        
        new_cols = [
            # Portfolio setup
            ("portfolios", "initial_balance", "FLOAT"),
            
            # Stock updates
            ("stocks", "sector", "VARCHAR(100)"),
            
            # Analysis technicals
            ("analyses", "rsi", "FLOAT"),
            ("analyses", "macd", "FLOAT"),
            ("analyses", "macd_signal", "FLOAT"),
            ("analyses", "bollinger_upper", "FLOAT"),
            ("analyses", "bollinger_lower", "FLOAT"),
            
            # Analysis fundamentals
            ("analyses", "market_cap", "VARCHAR(50)"),
            ("analyses", "pe_ratio", "FLOAT"),
            ("analyses", "peg_ratio", "FLOAT"),
            ("analyses", "analyst_recom", "FLOAT"),
            ("analyses", "institutional_ownership", "FLOAT"),
            ("analyses", "roe", "FLOAT"),
            ("analyses", "roa", "FLOAT"),
            ("analyses", "eps_growth_this_year", "FLOAT"),
            ("analyses", "eps_growth_next_year", "FLOAT"),
            
            # Analysis earnings & core financials
            ("analyses", "last_earnings_date", "DATETIME"),
            ("analyses", "next_earnings_date", "DATETIME"),
            ("analyses", "days_until_earnings", "INTEGER"),
            ("analyses", "revenue", "FLOAT"),
            ("analyses", "operating_income", "FLOAT"),
            ("analyses", "basic_eps", "FLOAT"),
            
            # Analysis extended metrics
            ("analyses", "analyst_source", "VARCHAR(50)"),
            ("analyses", "analysis_timestamp", "DATETIME"),
            ("analyses", "book_value", "FLOAT"),
            ("analyses", "free_cash_flow", "FLOAT"),
            ("analyses", "total_debt", "FLOAT"),
            ("analyses", "total_cash", "FLOAT"),
            ("analyses", "shares_outstanding", "INTEGER"),
            ("analyses", "earnings_growth", "FLOAT"),
            
            # Sentiment and targets
            ("analyses", "news_sentiment", "FLOAT"),
            ("analyses", "news_summary", "TEXT"),
            ("analyses", "median_price_target", "FLOAT")
        ]
        
        # Check existing columns to avoid redundant ALTER TABLE calls
        # We need to check columns for both 'stocks' and 'analyses'
        existing_cols_analyses = {col['name'] for col in inspector.get_columns('analyses')}
        existing_cols_stocks = {col['name'] for col in inspector.get_columns('stocks')}
        existing_cols_portfolios = {col['name'] for col in inspector.get_columns('portfolios')}
        
        with self.engine.connect() as conn:
            for table, col, col_type in new_cols:
                if table == 'stocks':
                    existing = existing_cols_stocks
                elif table == 'analyses':
                    existing = existing_cols_analyses
                elif table == 'portfolios':
                    existing = existing_cols_portfolios
                else:
                    existing = set()
                    
                if col not in existing:
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

    def get_all_portfolios(self, user_id: int, session: Session = None) -> list:
        """Get all portfolios from the database"""
        from .models import Portfolio
        if session:
            return session.query(Portfolio).filter(Portfolio.user_id == user_id).order_by(Portfolio.name).all()
            
        session = self.SessionLocal()
        try:
            return session.query(Portfolio).filter(Portfolio.user_id == user_id).order_by(Portfolio.name).all()
        except Exception as e:
            print(f"Error fetching portfolios: {e}")
            return []
        finally:
            session.close()
