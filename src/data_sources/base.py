"""Base classes for data sources using Strategy Pattern"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class DataSource(ABC):
    """Abstract base class for all data sources"""
    
    TIMEOUT = 15
    RETRY_COUNT = 2
    
    # Shared Circuit Breaker state across all instances & restarts
    _STATE_FILE = ".circuit_state.json"
    _CIRCUIT_STATE = {} 

    def _load_persistent_state(self):
        """Load state from disk to ensure persistence across restarts"""
        import json
        import os
        if not DataSource._CIRCUIT_STATE:
            if os.path.exists(DataSource._STATE_FILE):
                try:
                    with open(DataSource._STATE_FILE, "r") as f:
                        DataSource._CIRCUIT_STATE = json.load(f)
                except:
                    DataSource._CIRCUIT_STATE = {}

    def _save_persistent_state(self):
        """Save state to disk"""
        import json
        try:
            with open(DataSource._STATE_FILE, "w") as f:
                json.dump(DataSource._CIRCUIT_STATE, f)
        except: pass

    def _get_state(self) -> Dict[str, Any]:
        """Helper to get state for current source"""
        self._load_persistent_state()
        name = self.get_source_name()
        if name not in DataSource._CIRCUIT_STATE:
            DataSource._CIRCUIT_STATE[name] = {"broken_until": 0, "failure_count": 0}
        return DataSource._CIRCUIT_STATE[name]

    def is_broken(self) -> bool:
        """Check if the circuit is currently open (broken) for this source"""
        import time
        state = self._get_state()
        if state["broken_until"] > time.time():
            return True
        return False

    def _mark_broken(self, minutes: int = 10):
        """Break the circuit for a specific duration"""
        import time
        name = self.get_source_name()
        state = self._get_state()
        print(f"🚨 Circuit Breaker: Marking {name} as BROKEN for {minutes}m")
        state["broken_until"] = time.time() + (minutes * 60)
        self._save_persistent_state()

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
        Includes Circuit Breaker logic and SSL fallback.
        """
        if self.is_broken():
            return None

        from curl_cffi import requests
        import time
        
        request_kwargs = {
            "impersonate": "chrome110",
            "timeout": self.TIMEOUT
        }
        request_kwargs.update(kwargs)
        
        state = self._get_state()
        
        for attempt in range(self.RETRY_COUNT):
            try:
                response = requests.get(url, **request_kwargs)
                
                if response.status_code == 200:
                    state["failure_count"] = 0 # Reset on success
                    self._save_persistent_state()
                    return response
                
                if response.status_code == 403:
                    print(f"🚫 {self.get_source_name()} BLOCKED (403) for {url}")
                    self._mark_broken(30) # Break for 30m on 403
                    return None
                
                if response.status_code == 429:
                    time.sleep(2 * (attempt + 1))
                    continue
                    
            except Exception as e:
                error_msg = str(e).lower()
                # SSL Fallback triggered by specific certificate errors
                if any(x in error_msg for x in ["ssl", "certificate", "curl: (60)"]):
                    try:
                        print(f"⚠️ SSL Certificate issue detected for {url}. Attempting fallback with verify=False...")
                        fallback_kwargs = request_kwargs.copy()
                        fallback_kwargs["verify"] = False
                        response = requests.get(url, **fallback_kwargs)
                        if response.status_code == 200:
                            state["failure_count"] = 0
                            return response
                        
                        if response.status_code == 403:
                            self._mark_broken(30)
                            return None
                            
                        print(f"❌ SSL Fallback failed for {url} with status {response.status_code}")
                    except Exception as fe:
                        print(f"❌ SSL Fallback critical failure for {url}: {fe}")
                
                if attempt == self.RETRY_COUNT - 1:
                    # Multi-ticker sources like MarketPulse (Global Snapshot) shouldn't 
                    # trigger a full blackout just because one or two tickers time out.
                    if self.get_source_name() != "MarketPulse":
                        state["failure_count"] += 1
                        if state["failure_count"] >= 3:
                            self._mark_broken(10) # Break for 10m on repeated timeouts
                    
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
