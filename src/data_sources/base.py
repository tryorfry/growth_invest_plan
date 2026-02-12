"""Base classes for data sources using Strategy Pattern"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class DataSource(ABC):
    """Abstract base class for all data sources"""
    
    @abstractmethod
    async def fetch(self, ticker: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Fetch data for a given ticker symbol asynchronously.
        
        Args:
            ticker: Stock ticker symbol
            **kwargs: Additional parameters specific to the data source
            
        Returns:
            Dictionary containing fetched data or None if fetch fails
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return the name of this data source"""
        pass


class TechnicalDataSource(DataSource):
    """Base class for technical analysis data sources"""
    pass


class FundamentalDataSource(DataSource):
    """Base class for fundamental data sources"""
    pass


class AnalystDataSource(DataSource):
    """Base class for analyst sentiment data sources"""
    pass
