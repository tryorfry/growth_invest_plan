"""Configuration management for the application"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # Email Configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    ALERT_EMAIL_FROM = os.getenv('ALERT_EMAIL_FROM', SMTP_USERNAME)
    ALERT_EMAIL_TO = os.getenv('ALERT_EMAIL_TO', SMTP_USERNAME)
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'stock_analysis.db')
    
    # Alert Settings
    ENABLE_EMAIL_ALERTS = os.getenv('ENABLE_EMAIL_ALERTS', 'true').lower() == 'true'
    ALERT_CHECK_INTERVAL_MINUTES = int(os.getenv('ALERT_CHECK_INTERVAL_MINUTES', '60'))
    
    # API Keys (optional)
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
    POLYGON_API_KEY = os.getenv('POLYGON_API_KEY', '')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if cls.ENABLE_EMAIL_ALERTS and not cls.SMTP_USERNAME:
            print("Warning: Email alerts enabled but SMTP_USERNAME not configured")
        return True

# Validate configuration on import
Config.validate()
