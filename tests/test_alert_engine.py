"""Unit tests for alert engine"""

import pytest
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import Database
from src.alerts.alert_engine import AlertEngine
from src.models import Stock, Alert, AlertHistory
from src.analyzer import StockAnalysis


@pytest.fixture
def db():
    """Create test database"""
    db = Database(":memory:")  # In-memory database for testing
    db.init_db()
    return db


@pytest.fixture
def alert_engine():
    """Create alert engine instance"""
    return AlertEngine(use_email=False)  # Disable email for tests


@pytest.fixture
def sample_stock(db):
    """Create a sample stock in database"""
    with db.get_session() as session:
        stock = Stock(ticker="TEST", name="Test Stock", sector="Technology")
        session.add(stock)
        session.commit()
        return stock.id


@pytest.fixture
def sample_analysis():
    """Create sample stock analysis"""
    return StockAnalysis(
        ticker="TEST",
        timestamp=datetime.now(),
        current_price=150.0,
        rsi=65.0,
        macd=2.5,
        company_name="Test Stock"
    )


def test_create_alert(db, alert_engine, sample_stock):
    """Test creating an alert"""
    with db.get_session() as session:
        alert = alert_engine.create_alert(
            session,
            ticker="TEST",
            alert_type="price",
            condition="above",
            threshold=200.0,
            user_id=1,
            email_enabled=True
        )
        
        assert alert is not None
        assert alert.alert_type == "price"
        assert alert.condition == "above"
        assert alert.threshold == 200.0
        assert alert.is_active == 1


def test_price_alert_above(db, alert_engine, sample_stock, sample_analysis):
    """Test price alert with 'above' condition"""
    with db.get_session() as session:
        # Create alert for price above 100
        alert_engine.create_alert(
            session, "TEST", "price", "above", 100.0, user_id=1
        )
        
        # Current price is 150, should trigger
        sample_analysis.current_price = 150.0
        triggered = alert_engine.check_alerts(session, sample_analysis)
        
        assert len(triggered) == 1
        assert triggered[0]['alert_type'] == 'price'


def test_price_alert_below(db, alert_engine, sample_stock, sample_analysis):
    """Test price alert with 'below' condition"""
    with db.get_session() as session:
        # Create alert for price below 200
        alert_engine.create_alert(
            session, "TEST", "price", "below", 200.0, user_id=1
        )
        
        # Current price is 150, should trigger
        sample_analysis.current_price = 150.0
        triggered = alert_engine.check_alerts(session, sample_analysis)
        
        assert len(triggered) == 1


def test_rsi_alert_overbought(db, alert_engine, sample_stock, sample_analysis):
    """Test RSI overbought alert"""
    with db.get_session() as session:
        # Create alert for RSI above 70
        alert_engine.create_alert(
            session, "TEST", "rsi", "above", 70.0, user_id=1
        )
        
        # RSI is 75, should trigger
        sample_analysis.rsi = 75.0
        triggered = alert_engine.check_alerts(session, sample_analysis)
        
        assert len(triggered) == 1
        assert 'OVERBOUGHT' in triggered[0]['message']


def test_rsi_alert_oversold(db, alert_engine, sample_stock, sample_analysis):
    """Test RSI oversold alert"""
    with db.get_session() as session:
        # Create alert for RSI below 30
        alert_engine.create_alert(
            session, "TEST", "rsi", "below", 30.0, user_id=1
        )
        
        # RSI is 25, should trigger
        sample_analysis.rsi = 25.0
        triggered = alert_engine.check_alerts(session, sample_analysis)
        
        assert len(triggered) == 1
        assert 'OVERSOLD' in triggered[0]['message']


def test_deactivate_alert(db, alert_engine, sample_stock):
    """Test deactivating an alert"""
    with db.get_session() as session:
        alert = alert_engine.create_alert(
            session, "TEST", "price", "above", 200.0, user_id=1
        )
        
        assert alert.is_active == 1
        
        alert_engine.deactivate_alert(session, alert.id)
        
        session.refresh(alert)
        assert alert.is_active == 0


def test_alert_history_created(db, alert_engine, sample_stock, sample_analysis):
    """Test that alert history is created when alert triggers"""
    with db.get_session() as session:
        alert_engine.create_alert(
            session, "TEST", "price", "above", 100.0, user_id=1
        )
        
        sample_analysis.current_price = 150.0
        alert_engine.check_alerts(session, sample_analysis)
        
        # Check history
        from src.models import AlertHistory
        history = session.query(AlertHistory).all()
        assert len(history) == 1
        assert history[0].value == 150.0


def test_multiple_alerts(db, alert_engine, sample_stock, sample_analysis):
    """Test multiple alerts triggering"""
    with db.get_session() as session:
        # Create multiple alerts
        alert_engine.create_alert(session, "TEST", "price", "above", 100.0, user_id=1)
        alert_engine.create_alert(session, "TEST", "rsi", "above", 60.0, user_id=1)
        
        sample_analysis.current_price = 150.0
        sample_analysis.rsi = 65.0
        
        triggered = alert_engine.check_alerts(session, sample_analysis)
        
        assert len(triggered) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
