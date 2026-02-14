"""Alerts configuration page for Streamlit dashboard"""

import streamlit as st
import pandas as pd
from datetime import datetime
from src.database import Database
from src.alerts.alert_engine import AlertEngine
from src.models import Alert, AlertHistory
from sqlalchemy import desc


def render_alerts_page():
    """Render the alerts configuration and history page"""
    st.title("🔔 Alert Management")
    
    # Initialize
    db = st.session_state.get('db')
    if not db:
        db = Database()
        st.session_state['db'] = db
    
    alert_engine = AlertEngine(use_email=True)
    session = db.SessionLocal()
    
    try:
        # Tabs
        tab1, tab2, tab3 = st.tabs(["📢 Create Alert", "📋 Active Alerts", "📜 Alert History"])
        
        # Tab 1: Create Alert
        with tab1:
            st.subheader("Create New Alert")
            
            col1, col2 = st.columns(2)
            
            with col1:
                ticker = st.text_input("Stock Ticker").upper()
                alert_type = st.selectbox(
                    "Alert Type",
                    options=['price', 'rsi', 'macd', 'volume', 'earnings']
                )
                condition = st.selectbox(
                    "Condition",
                    options=['above', 'below', 'crosses_above', 'crosses_below']
                )
            
            with col2:
                threshold = st.number_input("Threshold Value", value=0.0, step=0.1)
                email_enabled = st.checkbox("Send Email Notifications", value=True)
                
                st.markdown("---")
                
                # Alert type descriptions
                descriptions = {
                    'price': 'Alert when stock price meets condition',
                    'rsi': 'Alert when RSI (0-100) meets condition. 70+ = overbought, 30- = oversold',
                    'macd': 'Alert when MACD value meets condition',
                    'volume': 'Alert when trading volume meets condition',
                    'earnings': 'Alert when days until earnings meets condition'
                }
                st.info(descriptions.get(alert_type, ''))
            
            if st.button("Create Alert", type="primary"):
                if ticker:
                    alert = alert_engine.create_alert(
                        session,
                        ticker=ticker,
                        alert_type=alert_type,
                        condition=condition,
                        threshold=threshold,
                        email_enabled=email_enabled
                    )
                    if alert:
                        st.success(f"✅ Created {alert_type} alert for {ticker}")
                    else:
                        st.error(f"Failed to create alert. Stock {ticker} may not exist in database.")
                else:
                    st.error("Please enter a ticker symbol")
        
        # Tab 2: Active Alerts
        with tab2:
            st.subheader("Active Alerts")
            
            # Get all active alerts
            alerts = session.query(Alert).filter(Alert.is_active == 1).all()
            
            if alerts:
                for alert in alerts:
                    with st.container():
                        col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
                        
                        # Get stock ticker
                        ticker = alert.stock.ticker if alert.stock else "Unknown"
                        
                        with col1:
                            st.markdown(f"**{ticker}**")
                            st.caption(f"Type: {alert.alert_type}")
                        
                        with col2:
                            st.text(f"{alert.condition}")
                            st.caption(f"Threshold: {alert.threshold}")
                        
                        with col3:
                            if alert.last_triggered:
                                st.caption(f"Last triggered: {alert.last_triggered.strftime('%Y-%m-%d %H:%M')}")
                            else:
                                st.caption("Never triggered")
                            
                            email_status = "📧 Email ON" if alert.email_enabled else "📧 Email OFF"
                            st.caption(email_status)
                        
                        with col4:
                            if st.button("🗑️", key=f"del_alert_{alert.id}"):
                                alert_engine.deactivate_alert(session, alert.id)
                                st.success("Alert deactivated")
                                st.rerun()
                        
                        st.markdown("---")
            else:
                st.info("No active alerts. Create one in the 'Create Alert' tab!")
        
        # Tab 3: Alert History
        with tab3:
            st.subheader("Alert History")
            
            # Get recent alert history
            history = session.query(AlertHistory).order_by(
                desc(AlertHistory.triggered_at)
            ).limit(50).all()
            
            if history:
                history_data = []
                for h in history:
                    alert = h.alert
                    ticker = alert.stock.ticker if alert and alert.stock else "Unknown"
                    
                    history_data.append({
                        'Time': h.triggered_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'Ticker': ticker,
                        'Type': alert.alert_type if alert else 'N/A',
                        'Value': f"{h.value:.2f}" if h.value else 'N/A',
                        'Message': h.message[:50] + '...' if h.message and len(h.message) > 50 else h.message,
                        'Notified': '✅' if h.notification_sent else '❌'
                    })
                
                df = pd.DataFrame(history_data)
                st.dataframe(df, width='stretch')
            else:
                st.info("No alert history yet.")
    finally:
        session.close()


if __name__ == "__main__":
    render_alerts_page()
