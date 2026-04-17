"""Standardized application exceptions for Growth Investment Analyzer"""

class AppError(Exception):
    """Base class for all application errors"""
    def __init__(self, message: str, ticker: str = None):
        super().__init__(message)
        self.message = message
        self.ticker = ticker

class DataFetchError(AppError):
    """Raised when an external data fetch fails critically"""
    pass

class AuthError(AppError):
    """Raised for authentication or permission failures"""
    pass

class ValidationError(AppError):
    """Raised when ticker or user input validation fails"""
    pass
