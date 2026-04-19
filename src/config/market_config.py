"""Centralized configuration for Global Market Pulsing and Snapshots"""

# --- MARKET GROUPINGS ---
MARKET_GROUPS = {
    "🇺🇸 US & 🪙 Crypto": ["S&P 500", "Nasdaq", "Dow Jones", "Bitcoin", "Ethereum"],
    "🇬🇧 Europe & 🇦🇺 Pacific": ["FTSE 100", "DAX 40", "ASX 200"],
    "🈯 Asia": ["Nikkei 225", "Hang Seng", "Straits Times", "SGX", "Nifty 50"],
    "📦 Commodities": ["Crude Oil", "Gold", "Silver"],
    "💱 Forex": ["USD Index", "USD/SGD", "XAU/USD"]
}

# --- TICKER CONFIGURATION ---
# symbol: yfinance ticker
# display_name: Label used in UI
# type: Index, Crypto, Commodity, Forex
# on_map: Boolean to show on Pulse Map
TICKER_CONFIG = {
    "^GSPC": {"name": "S&P 500", "short": "SPX", "type": "Index", "on_map": True, "lat": 38.50, "lon": -98.00, "country": "USA"},
    "^IXIC": {"name": "Nasdaq", "short": "NDX", "type": "Index", "on_map": True, "lat": 42.00, "lon": -115.00, "country": "USA"},
    "^DJI":  {"name": "Dow Jones", "short": "DJI", "type": "Index", "on_map": True, "lat": 32.00, "lon": -100.00, "country": "USA"},
    "^FTSE": {"name": "FTSE 100", "short": "FTSE", "type": "Index", "on_map": True, "lat": 55.37, "lon": -3.43, "country": "UK"},
    "^GDAXI": {"name": "DAX 40", "short": "DAX", "type": "Index", "on_map": True, "lat": 51.16, "lon": 10.45, "country": "Germany"},
    "^N225": {"name": "Nikkei 225", "short": "N225", "type": "Index", "on_map": True, "lat": 36.20, "lon": 138.25, "country": "Japan"},
    "^HSI":  {"name": "Hang Seng", "short": "HSI", "type": "Index", "on_map": True, "lat": 22.31, "lon": 114.16, "country": "Hong Kong"},
    "^STI":  {"name": "Straits Times", "short": "STI", "type": "Index", "on_map": True, "lat": 1.35, "lon": 103.81, "country": "Singapore"},
    "S68.SI": {"name": "SGX", "short": "SGX", "type": "Index", "on_map": True, "lat": -2.00, "lon": 108.00, "country": "Singapore"},
    "^NSEI": {"name": "Nifty 50", "short": "NIFTY", "type": "Index", "on_map": True, "lat": 20.59, "lon": 78.96, "country": "India"},
    "^AXJO": {"name": "ASX 200", "short": "ASX", "type": "Index", "on_map": True, "lat": -25.27, "lon": 133.77, "country": "Australia"},
    
    # Non-Map Assets
    "BTC-USD": {"name": "Bitcoin", "short": "BTC", "type": "Crypto", "on_map": False},
    "ETH-USD": {"name": "Ethereum", "short": "ETH", "type": "Crypto", "on_map": False},
    
    # Commodities
    "CL=F": {"name": "Crude Oil", "short": "OIL", "type": "Commodity", "on_map": False},
    "GC=F": {"name": "Gold", "short": "GLD", "type": "Commodity", "on_map": False},
    "SI=F": {"name": "Silver", "short": "SLV", "type": "Commodity", "on_map": False},
    
    # Forex
    "DX-Y.NYB": {"name": "USD Index", "short": "DXY", "type": "Forex", "on_map": False},
    "USDSGD=X": {"name": "USD/SGD", "short": "USDSGD", "type": "Forex", "on_map": False},
    "XAUUSD=X": {"name": "XAU/USD", "short": "XAU", "type": "Forex", "on_map": False}
}

def get_snapshot_tickers():
    """Returns tickers organized by their regional groups"""
    return TICKER_CONFIG

def get_map_tickers():
    """Returns only indices designed to be plotted on the world map"""
    return {k: v for k, v in TICKER_CONFIG.items() if v.get('on_map')}
