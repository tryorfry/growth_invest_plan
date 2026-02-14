"""Alert engine for evaluating and triggering stock alerts"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models import Alert, AlertHistory, Stock, Analysis
from ..analyzer import StockAnalysis
from .notifiers import EmailNotifier, ConsoleNotifier


class AlertEngine:
    """Evaluate stock conditions and trigger alerts"""
    
    def __init__(self, use_email: bool = True):
        self.email_notifier = EmailNotifier() if use_email else None
        self.console_notifier = ConsoleNotifier()
    
    def check_alerts(self, session: Session, analysis: StockAnalysis) -> List[Dict[str, Any]]:
        """
        Check all active alerts for a stock and trigger if conditions are met.
        
        Args:
            session: Database session
            analysis: StockAnalysis object with current data
            
        Returns:
            List of triggered alerts
        """
        # Get stock from database
        stock = session.query(Stock).filter(Stock.ticker == analysis.ticker).first()
        if not stock:
            return []
        
        # Get all active alerts for this stock
        alerts = session.query(Alert).filter(
            Alert.stock_id == stock.id,
            Alert.is_active == 1
        ).all()
        
        triggered = []
        
        for alert in alerts:
            result = self._evaluate_alert(alert, analysis, session)
            if result:
                triggered.append(result)
        
        return triggered
    
    def _evaluate_alert(self, alert: Alert, analysis: StockAnalysis, session: Session) -> Optional[Dict[str, Any]]:
        """Evaluate a single alert condition"""
        
        # Get the current value based on alert type
        current_value = self._get_alert_value(alert.alert_type, analysis)
        if current_value is None:
            return None
        
        # Check if condition is met
        is_triggered = False
        
        if alert.condition == 'above':
            is_triggered = current_value > alert.threshold
        elif alert.condition == 'below':
            is_triggered = current_value < alert.threshold
        elif alert.condition == 'crosses_above':
            # Check if crossed above since last check
            is_triggered = self._check_crossover(alert, current_value, alert.threshold, 'above', session)
        elif alert.condition == 'crosses_below':
            # Check if crossed below since last check
            is_triggered = self._check_crossover(alert, current_value, alert.threshold, 'below', session)
        
        if is_triggered:
            return self._trigger_alert(alert, current_value, analysis, session)
        
        return None
    
    def _get_alert_value(self, alert_type: str, analysis: StockAnalysis) -> Optional[float]:
        """Get the current value for the alert type"""
        value_map = {
            'price': analysis.current_price,
            'rsi': analysis.rsi,
            'macd': analysis.macd,
            'volume': getattr(analysis.history.iloc[-1], 'Volume', None) if analysis.history is not None else None,
            'earnings': analysis.days_until_earnings
        }
        return value_map.get(alert_type)
    
    def _check_crossover(self, alert: Alert, current_value: float, threshold: float, direction: str, session: Session) -> bool:
        """Check if value crossed threshold since last trigger"""
        # Get last history entry for this alert
        last_history = session.query(AlertHistory).filter(
            AlertHistory.alert_id == alert.id
        ).order_by(AlertHistory.triggered_at.desc()).first()
        
        if not last_history:
            # No previous trigger, check if currently on the right side
            if direction == 'above':
                return current_value > threshold
            else:
                return current_value < threshold
        
        # Check if crossed
        last_value = last_history.value
        if direction == 'above':
            return last_value <= threshold and current_value > threshold
        else:
            return last_value >= threshold and current_value < threshold
    
    def _trigger_alert(self, alert: Alert, value: float, analysis: StockAnalysis, session: Session) -> Dict[str, Any]:
        """Trigger an alert and send notifications"""
        
        # Create alert message
        message = self._create_alert_message(alert, value, analysis)
        
        # Save to history
        history = AlertHistory(
            alert_id=alert.id,
            triggered_at=datetime.now(),
            value=value,
            message=message,
            notification_sent=0
        )
        session.add(history)
        
        # Update last triggered time
        alert.last_triggered = datetime.now()
        
        # Send notifications
        notification_sent = False
        if alert.email_enabled and self.email_notifier:
            subject = f"{analysis.ticker} Alert: {alert.alert_type.upper()}"
            notification_sent = self.email_notifier.send_alert(subject, message, analysis.ticker)
        
        # Always send to console
        self.console_notifier.send_alert(
            f"{analysis.ticker} {alert.alert_type.upper()} Alert",
            message,
            analysis.ticker
        )
        
        history.notification_sent = 1 if notification_sent else 0
        session.commit()
        
        return {
            'alert_id': alert.id,
            'ticker': analysis.ticker,
            'alert_type': alert.alert_type,
            'condition': alert.condition,
            'threshold': alert.threshold,
            'current_value': value,
            'message': message,
            'notification_sent': notification_sent
        }
    
    def _create_alert_message(self, alert: Alert, value: float, analysis: StockAnalysis) -> str:
        """Create a human-readable alert message"""
        
        alert_type_names = {
            'price': 'Price',
            'rsi': 'RSI',
            'macd': 'MACD',
            'volume': 'Volume',
            'earnings': 'Days Until Earnings'
        }
        
        type_name = alert_type_names.get(alert.alert_type, alert.alert_type)
        
        if alert.condition in ['above', 'crosses_above']:
            condition_text = 'is above' if alert.condition == 'above' else 'crossed above'
        else:
            condition_text = 'is below' if alert.condition == 'below' else 'crossed below'
        
        message = f"{type_name} {condition_text} {alert.threshold:.2f}\n"
        message += f"Current value: {value:.2f}\n"
        message += f"\nCurrent Price: ${analysis.current_price:.2f}\n"
        
        if alert.alert_type == 'rsi':
            if value > 70:
                message += "⚠️ Stock is OVERBOUGHT\n"
            elif value < 30:
                message += "⚠️ Stock is OVERSOLD\n"
        
        if alert.alert_type == 'earnings' and value < 7:
            message += "⚠️ Earnings announcement is approaching soon!\n"
        
        return message
    
    def create_alert(self, session: Session, ticker: str, alert_type: str, 
                    condition: str, threshold: float, email_enabled: bool = True) -> Optional[Alert]:
        """
        Create a new alert.
        
        Args:
            session: Database session
            ticker: Stock ticker
            alert_type: Type of alert (price, rsi, macd, volume, earnings)
            condition: Condition (above, below, crosses_above, crosses_below)
            threshold: Threshold value
            email_enabled: Whether to send email notifications
            
        Returns:
            Created Alert object or None if stock not found
        """
        stock = session.query(Stock).filter(Stock.ticker == ticker).first()
        if not stock:
            return None
        
        alert = Alert(
            stock_id=stock.id,
            alert_type=alert_type,
            condition=condition,
            threshold=threshold,
            is_active=1,
            email_enabled=1 if email_enabled else 0
        )
        
        session.add(alert)
        session.commit()
        
        return alert
    
    def deactivate_alert(self, session: Session, alert_id: int):
        """Deactivate an alert"""
        alert = session.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.is_active = 0
            session.commit()
