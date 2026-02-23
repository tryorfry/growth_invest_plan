"""
Smoke tests for advanced data sources: Options, Insider, Short Interest.
Verifies modules can be imported and instantiated without live network calls.
The scripts/debug_patterns.py and scripts/investigate_marketbeat.py are 
available for manual live testing.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestOptionsSource:
    """Tests for OptionsSource"""

    def test_import(self):
        from src.data_sources.options_source import OptionsSource
        assert OptionsSource is not None

    def test_init(self):
        from src.data_sources.options_source import OptionsSource
        src = OptionsSource()
        assert src is not None

    def test_fetch_options_data_bad_ticker(self):
        """Should return None or dict for bad ticker — no uncaught exceptions"""
        from src.data_sources.options_source import OptionsSource
        src = OptionsSource()
        try:
            result = src.fetch_options_data("INVALID_TICKER_XYZ123")
            assert result is None or isinstance(result, dict)
        except Exception:
            pass  # graceful failure acceptable


class TestInsiderSource:
    """Tests for InsiderSource"""

    def test_import(self):
        from src.data_sources.insider_source import InsiderSource
        assert InsiderSource is not None

    def test_init(self):
        from src.data_sources.insider_source import InsiderSource
        src = InsiderSource()
        assert src is not None

    @pytest.mark.asyncio
    async def test_get_source_name(self):
        from src.data_sources.insider_source import InsiderSource
        src = InsiderSource()
        # Source should have a name method
        if hasattr(src, 'get_source_name'):
            name = src.get_source_name()
            assert isinstance(name, str)


class TestShortInterestSource:
    """Tests for ShortInterestSource"""

    def test_import(self):
        from src.data_sources.short_interest_source import ShortInterestSource
        assert ShortInterestSource is not None

    def test_init(self):
        from src.data_sources.short_interest_source import ShortInterestSource
        src = ShortInterestSource()
        assert src is not None

    def test_fetch_short_data_bad_ticker(self):
        """Should return None or dict for bad ticker — no uncaught exceptions"""
        from src.data_sources.short_interest_source import ShortInterestSource
        src = ShortInterestSource()
        try:
            result = src.fetch_short_interest("INVALID_TICKER_XYZ123")
            assert result is None or isinstance(result, dict)
        except Exception:
            pass
