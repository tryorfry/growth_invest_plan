"""Email notification system for alerts"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional
from ..config import Config


class EmailNotifier:
    """Send email notifications for alerts"""
    
    def __init__(self):
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.username = Config.SMTP_USERNAME
        self.password = Config.SMTP_PASSWORD
        self.from_email = Config.ALERT_EMAIL_FROM
        self.to_email = Config.ALERT_EMAIL_TO
    
    def send_alert(self, subject: str, message: str, ticker: str = None) -> bool:
        """
        Send an email alert.
        
        Args:
            subject: Email subject
            message: Email body
            ticker: Stock ticker (optional)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not Config.ENABLE_EMAIL_ALERTS:
            print(f"Email alerts disabled. Would have sent: {subject}")
            return False
        
        if not self.username or not self.password:
            print("Email credentials not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[Stock Alert] {subject}"
            msg['From'] = self.from_email
            msg['To'] = self.to_email
            
            # Create HTML and plain text versions
            text_body = f"""
Stock Alert Notification
========================

{message}

Ticker: {ticker or 'N/A'}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
This is an automated alert from your Stock Analysis Tool.
"""
            
            html_body = f"""
<html>
  <head></head>
  <body>
    <h2>Stock Alert Notification</h2>
    <p>{message.replace(chr(10), '<br>')}</p>
    <p><strong>Ticker:</strong> {ticker or 'N/A'}</p>
    <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <hr>
    <p><small>This is an automated alert from your Stock Analysis Tool.</small></p>
  </body>
</html>
"""
            
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            print(f"✅ Alert email sent: {subject}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email alert: {e}")
            return False
    
    def send_daily_summary(self, watchlist_data: dict) -> bool:
        """Send daily summary of watchlist stocks"""
        subject = "Daily Watchlist Summary"
        
        message_parts = ["Daily Summary of Your Watchlist:\n"]
        for ticker, data in watchlist_data.items():
            price = data.get('price', 'N/A')
            change = data.get('change', 0)
            change_pct = data.get('change_pct', 0)
            
            message_parts.append(
                f"\n{ticker}: ${price} ({change_pct:+.2f}%)"
            )
        
        message = "\n".join(message_parts)
        return self.send_alert(subject, message)


class ConsoleNotifier:
    """Print notifications to console (for testing)"""
    
    def send_alert(self, subject: str, message: str, ticker: str = None) -> bool:
        """Print alert to console"""
        print(f"\n{'='*60}")
        print(f"🔔 ALERT: {subject}")
        print(f"{'='*60}")
        print(f"Ticker: {ticker or 'N/A'}")
        print(f"Message: {message}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        return True
