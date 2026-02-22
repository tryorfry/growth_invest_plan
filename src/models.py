"""Database models for stock analysis persistence"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """User account for the platform"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    tier = Column(String(20), default='free') # 'free', 'premium', 'admin'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(username='{self.username}', tier='{self.tier}')>"


class Stock(Base):
    """Stock entity with basic information"""
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255))
    sector = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analyses = relationship("Analysis", back_populates="stock", cascade="all, delete-orphan")
    news_items = relationship("News", back_populates="stock", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Stock(ticker='{self.ticker}', name='{self.name}')>"


class Analysis(Base):
    """Stock analysis snapshot with technical and fundamental data"""
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    analysis_timestamp = Column(DateTime)  # Actual time of analysis
    
    # Price data
    current_price = Column(Float)
    open_price = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    
    # Technical indicators
    atr = Column(Float)
    ema20 = Column(Float)
    ema50 = Column(Float)
    ema200 = Column(Float)
    rsi = Column(Float)  # New indicator
    macd = Column(Float)  # New indicator
    macd_signal = Column(Float)  # New indicator
    bollinger_upper = Column(Float)  # New indicator
    bollinger_lower = Column(Float)  # New indicator
    
    # Earnings
    last_earnings_date = Column(DateTime)
    next_earnings_date = Column(DateTime)
    days_until_earnings = Column(Integer)
    
    # Financials
    revenue = Column(Float)
    operating_income = Column(Float)
    basic_eps = Column(Float)
    
    # Fundamental metrics (from Finviz)
    market_cap = Column(String(50))
    pe_ratio = Column(Float)
    peg_ratio = Column(Float)
    analyst_recom = Column(Float)
    institutional_ownership = Column(Float)
    roe = Column(Float)
    roa = Column(Float)
    eps_growth_this_year = Column(Float)
    eps_growth_next_year = Column(Float)
    
    # Analyst targets
    median_price_target = Column(Float)
    analyst_source = Column(String(50))  # Track source (MarketBeat/YFinance)
    
    # Valuation data
    book_value = Column(Float)
    free_cash_flow = Column(Float)
    total_debt = Column(Float)
    total_cash = Column(Float)
    shares_outstanding = Column(Integer)
    earnings_growth = Column(Float)
    
    # Sentiment
    news_sentiment = Column(Float)
    news_summary = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="analyses")
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('ix_stock_timestamp', 'stock_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<Analysis(stock_id={self.stock_id}, timestamp='{self.timestamp}', price={self.current_price})>"


class News(Base):
    """News articles with sentiment analysis"""
    __tablename__ = 'news'
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    headline = Column(Text, nullable=False)
    url = Column(Text)
    published_date = Column(DateTime, index=True)
    sentiment_score = Column(Float)  # -1 to 1
    source = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="news_items")
    
    def __repr__(self):
        return f"<News(stock_id={self.stock_id}, headline='{self.headline[:50]}...', sentiment={self.sentiment_score})>"


class Watchlist(Base):
    """User watchlist for tracking stocks"""
    __tablename__ = 'watchlists'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, default=1)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Watchlist(name='{self.name}', items={len(self.items)})>"


class WatchlistItem(Base):
    """Individual stock in a watchlist"""
    __tablename__ = 'watchlist_items'
    
    id = Column(Integer, primary_key=True)
    watchlist_id = Column(Integer, ForeignKey('watchlists.id'), nullable=False)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    
    # Relationships
    watchlist = relationship("Watchlist", back_populates="items")
    stock = relationship("Stock")
    
    # Unique constraint: one stock per watchlist
    __table_args__ = (
        Index('ix_watchlist_stock', 'watchlist_id', 'stock_id', unique=True),
    )
    
    def __repr__(self):
        return f"<WatchlistItem(watchlist_id={self.watchlist_id}, stock_id={self.stock_id})>"


class Alert(Base):
    """Alert configuration for stock conditions"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, default=1)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    alert_type = Column(String(50), nullable=False)  # price, rsi, macd, volume, earnings
    condition = Column(String(50), nullable=False)  # above, below, crosses_above, crosses_below
    threshold = Column(Float)  # threshold value
    is_active = Column(Integer, default=1)  # 1=active, 0=inactive
    email_enabled = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime)
    
    # Relationships
    stock = relationship("Stock")
    history = relationship("AlertHistory", back_populates="alert", cascade="all, delete-orphan")
    
    # Index for active alerts
    __table_args__ = (
        Index('ix_active_alerts', 'is_active', 'stock_id'),
    )
    
    def __repr__(self):
        return f"<Alert(stock_id={self.stock_id}, type='{self.alert_type}', condition='{self.condition}', threshold={self.threshold})>"


class AlertHistory(Base):
    """History of triggered alerts"""
    __tablename__ = 'alert_history'
    
    id = Column(Integer, primary_key=True)
    alert_id = Column(Integer, ForeignKey('alerts.id'), nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    value = Column(Float)  # actual value that triggered the alert
    message = Column(Text)
    notification_sent = Column(Integer, default=0)  # 0=not sent, 1=sent
    
    # Relationships
    alert = relationship("Alert", back_populates="history")
    
    def __repr__(self):
        return f"<AlertHistory(alert_id={self.alert_id}, triggered_at='{self.triggered_at}', value={self.value})>"


class Portfolio(Base):
    """Investment portfolio container"""
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, default=1)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    currency = Column(String(10), default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Portfolio(name='{self.name}')>"


class Transaction(Base):
    """Individual trade record"""
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    type = Column(String(10), nullable=False)  # BUY, SELL, DIVIDEND
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    fees = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    notes = Column(Text)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")
    stock = relationship("Stock")
    
    def __repr__(self):
        return f"<Transaction(type='{self.type}', price={self.price}, qty={self.quantity})>"
