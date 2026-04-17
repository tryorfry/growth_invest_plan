"""Base classes for data sources using Strategy Pattern"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class DataSource(ABC):
    """Abstract base class for all data sources"""
    
    TIMEOUT = 15
    RETRY_COUNT = 2

    @abstractmethod
    async def fetch(self, ticker: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Fetch data for a given ticker symbol asynchronously.
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return the name of this data source"""
        pass

    def _get_response_sync(self, url: str, **kwargs) -> Optional[Any]:
        """
        Synchronous request helper that returns a full Response object.
        Used by subclasses that need metadata (e.g., redirect URL).
        """
        from curl_cffi import requests
        import time
        
        request_kwargs = {
            "impersonate": "chrome110",
            "timeout": self.TIMEOUT
        }
        request_kwargs.update(kwargs)
        
        for attempt in range(self.RETRY_COUNT):
            try:
                response = requests.get(url, **request_kwargs)
                if response.status_code == 200:
                    return response
                
                if response.status_code in [403, 429]:
                    time.sleep(2 * (attempt + 1))
                    continue
                    
            except Exception as e:
                # SSL Fallback
                if "SSL" in str(e) or "certificate" in str(e).lower():
                    try:
                        fallback_kwargs = request_kwargs.copy()
                        fallback_kwargs["verify"] = False
                        response = requests.get(url, **fallback_kwargs)
                        if response.status_code == 200:
                            return response
                    except Exception:
                        pass
                
                if attempt == self.RETRY_COUNT - 1:
                    print(f"Error: {self.get_source_name()} failed for {url}: {e}")
        
        return None

    async def _make_request(self, url: str, **kwargs) -> Optional[str]:
        """Simplified async string helper"""
        # (Internal implementation remains similar but calls an async version of _get_response)
        # For now, we'll implement it directly to avoid excess complexity
        import asyncio
        loop = asyncio.get_running_loop()
        resp = await loop.run_in_executor(None, lambda: self._get_response_sync(url, **kwargs))
        return resp.text if resp else None

    def _make_request_sync(self, url: str, **kwargs) -> Optional[str]:
        """Simplified sync string helper"""
        resp = self._get_response_sync(url, **kwargs)
        return resp.text if resp else None


class TechnicalDataSource(DataSource):
    """Base class for technical analysis data sources"""
    pass


class FundamentalDataSource(DataSource):
    """Base class for fundamental data sources"""
    pass


class AnalystDataSource(DataSource):
    """Base class for analyst sentiment data sources"""
    pass
