"""Database models for stock analysis persistence"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


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
