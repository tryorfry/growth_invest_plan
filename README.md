# Growth Investment Plan Analysis Tool

A comprehensive stock analysis tool that combines technical indicators, fundamental data, and analyst sentiment to help evaluate growth investment opportunities.

## 🚀 New Features

### 🔔 Alert System
- **Price Alerts:** Get notified when stocks hit target prices
- **Technical Alerts:** RSI overbought/oversold, MACD crossovers
- **Volume Alerts:** Unusual trading activity detection
- **Earnings Alerts:** Notifications for upcoming earnings
- **Email Notifications:** Gmail integration for instant alerts

### 📋 Watchlist Management
- **Create Multiple Watchlists:** Organize stocks by strategy or sector
- **Track Performance:** Monitor watchlist stocks in real-time
- **Add Notes:** Document your investment thesis
- **Quick Access:** View all watchlist stocks in dashboard

### 📊 Excel Export
- **Multi-Sheet Workbooks:** Separate sheets for each stock
- **Formatted Reports:** Professional styling and layout
- **Summary Tables:** Compare multiple stocks at a glance
- **Export Watchlists:** Save watchlist data to Excel

### 🔬 Advanced Analytics
- **Options Data:** Implied volatility, put/call ratio
- **Insider Trading:** Track insider buys/sells and ownership
- **Short Interest:** Short float %, days to cover, trends
- **Correlation Analysis:** See how stocks move together

### 📈 Enhanced Visualizations
- **Comparison Charts:** Overlay multiple stocks (normalized or absolute)
- **Correlation Heatmaps:** Visualize stock relationships
- **Performance Tables:** Compare returns across timeframes
- **Sector Heatmaps:** See sector performance at a glance
- **Pattern Recognition:** Detect candlestick patterns (Doji, Hammer, Engulfing, etc.)

### Interactive Web Dashboard
- **Streamlit-based UI** with real-time analysis
- **Interactive Plotly charts** with zoom, pan, and hover details
- **Toggleable indicators** (EMAs, RSI, MACD, Bollinger Bands)
- **Historical trend tracking** from database

### Database Persistence
- **SQLite database** for storing analysis history
- **Track performance** over time
- **Compare predictions** to actual results

### Advanced Technical Indicators
- **RSI** (Relative Strength Index) - Overbought/Oversold signals
- **MACD** (Moving Average Convergence Divergence) - Trend following
- **Bollinger Bands** - Volatility measurement

## Features

### 📊 Technical Analysis
- **ATR (Average True Range):** 14-day volatility measurement
- **EMAs (Exponential Moving Averages):** 20, 50, and 200-period trend indicators
- **RSI:** Momentum oscillator (0-100 scale)
- **MACD:** Trend strength and direction
- **Bollinger Bands:** Price volatility bands
- **Current Price Data:** Open, High, Low, Close with timestamps

### 💰 Fundamental Data (via Finviz)
- **Market Capitalization**
- **Analyst Recommendations** (1-5 scale: 1=Strong Buy, 5=Sell)
- **Institutional Ownership %**
- **Average Trading Volume**
- **Profitability Metrics:** ROE (Return on Equity), ROA (Return on Assets)
- **Growth Metrics:**
  - EPS Growth This Year
  - EPS Growth Next Year
  - EPS Growth Next 5 Years
- **Valuation:** P/E, Forward P/E, PEG Ratio

### 📰 News Sentiment Analysis
- AI-powered sentiment analysis of recent headlines
- Sentiment score and summary

### 📈 Analyst Targets
- Median price targets from MarketBeat (post-earnings)
- Upside/downside calculation

## Installation

### Prerequisites
- Python 3.10-3.13 (3.14 not supported due to dependency constraints)
- Git (optional)

### Setup

1. **Clone or Download** the repository

2. **Create Virtual Environment:**
   ```bash
   python -m venv .venv
   ```

3. **Activate Virtual Environment:**
   - **Windows (PowerShell):**
     ```bash
     .venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD):**
     ```bash
     .venv\Scripts\activate.bat
     ```
   - **macOS/Linux:**
     ```bash
     source .venv/bin/activate
     ```

4. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Web Dashboard (Recommended)

Start the interactive dashboard:
```bash
streamlit run src/dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

**Features:**
- Enter ticker symbol in sidebar
- Click "Analyze" to fetch data
- Toggle indicators (EMAs, RSI, MACD, Bollinger Bands)
- View interactive charts with zoom/pan
- Explore fundamental data tables
- Track historical analyses

### Command Line Interface

Analyze stocks from the terminal:

```bash
# Single stock
python app.py AAPL

# Multiple stocks
python app.py AAPL NVDA GOOGL

# From file (one ticker per line)
python app.py --file tickers.txt

# Skip database storage
python app.py AAPL --no-db

# Custom CSV output
python app.py AAPL --csv my_results.csv
```

### Docker Usage

#### Using Docker Compose (Recommended)

Run both CLI and dashboard with a single command:

```bash
# Start the dashboard
docker-compose up dashboard

# Run CLI analysis
docker-compose run cli AAPL NVDA

# Stop all services
docker-compose down
```

## Advanced Features Usage

### Email Alerts Setup

1. **Configure Gmail App Password:**
   - Go to Google Account → Security → 2-Step Verification → App Passwords
   - Generate an app password for "Mail"
   - Update `.env` file with your credentials

2. **Create Alerts:**
```python
from src.database import Database
from src.alerts.alert_engine import AlertEngine

db = Database()
alert_engine = AlertEngine(use_email=True)

# Price alert
alert_engine.create_alert(
    db.get_session(), 
    ticker='AAPL', 
    alert_type='price', 
    condition='above', 
    threshold=300.0
)

# RSI alert (overbought)
alert_engine.create_alert(
    db.get_session(),
    ticker='NVDA',
    alert_type='rsi',
    condition='above',
    threshold=70.0
)
```

3. **Check Alerts:**
```bash
# Run test script
python test_features.py
```

### Watchlist Management

```python
from src.database import Database
from src.watchlist import WatchlistManager

db = Database()
wm = WatchlistManager(db.get_session())

# Create watchlist
watchlist = wm.create_watchlist("Growth Stocks", "High-growth tech stocks")

# Add stocks
wm.add_stock_to_watchlist(watchlist.id, "AAPL", "Strong fundamentals")
wm.add_stock_to_watchlist(watchlist.id, "NVDA", "AI leader")

# Get stocks
stocks = wm.get_watchlist_stocks(watchlist.id)
```

### Excel Export

```python
from src.analyzer import StockAnalyzer
from src.exporters.excel_exporter import ExcelExporter

analyzer = StockAnalyzer()
analyses = []

for ticker in ['AAPL', 'NVDA', 'GOOGL']:
    analysis = await analyzer.analyze(ticker)
    analyses.append(analysis)

exporter = ExcelExporter()
filename = exporter.export_analysis(analyses, "my_analysis.xlsx")
```

### Advanced Analytics

```python
from src.data_sources.options_source import OptionsSource
from src.data_sources.insider_source import InsiderSource
from src.data_sources.short_interest_source import ShortInterestSource

# Options data
options = OptionsSource()
data = options.fetch_options_data('AAPL')
print(f"IV: {data['implied_volatility']:.2%}")
print(f"Put/Call: {data['put_call_ratio']:.2f}")

# Insider trading
insider = InsiderSource()
data = await insider.fetch_insider_data('AAPL')
print(f"Insider Ownership: {data['insider_ownership_pct']:.2f}%")

# Short interest
short = ShortInterestSource()
data = short.fetch_short_interest('AAPL')
print(f"Short Float: {data['short_percent_of_float']:.2f}%")
```


#### Dashboard Only

```bash
# Build the dashboard image
docker build -f Dockerfile.dashboard -t growth-invest-plan:dashboard .

# Run the dashboard
docker run -p 8501:8501 growth-invest-plan:dashboard

# Access at http://localhost:8501
```

#### CLI Only

```bash
# Build the CLI image
docker build -t growth-invest-plan .

# Run analysis
docker run growth-invest-plan AAPL NVDA
```

**Note:** To persist data between runs, mount volumes:
```bash
docker run -v $(pwd)/stock_analysis.db:/app/stock_analysis.db \
           -v $(pwd)/charts:/app/charts \
           growth-invest-plan AAPL
```

**Output:**
- Console analysis summary
- Static chart images in `charts/` directory
- CSV export with all metrics
- Database storage (unless `--no-db` flag used)

## Sample Output

```
--- Analysis for AAPL (2026-02-13 00:00:00-05:00) ---
Current Price: 259.45
Open: 262.01 | High: 262.23 | Low: 258.80 | Close: 259.45
------------------------------
ATR (14):   6.78
EMA 20:     266.00
EMA 50:     265.21
EMA 200:    248.33
RSI:        45.32
MACD:       -2.15
Last Earnings: 2026-01-29

--- Finviz Data ---
Market Cap: 3828.99B
Analysts Recom: 2.02
Inst Own: 65.82%
Avg Volume: 48.51M
ROE: 152.02% | ROA: 32.56%
EPS Growth (This Y): 13.28%
EPS Growth (Next Y): 9.83%
EPS Growth (Next 5Y): 11.17%
P/E: 33.00 | Fwd P/E: 28.10 | PEG: 2.52

--- Fundamentals ---
Latest Revenue (Quarterly): $143.76B
Op Income (Quarterly): $50.85B
Basic EPS (Quarterly): 2.85
Next Earnings Date: 2026-05-01 (76 days left)
```

## Data Sources

- **yfinance:** Historical price data, technical indicators, financial statements, earnings dates
- **Finviz:** Fundamental metrics, analyst recommendations, growth projections
- **MarketBeat:** Post-earnings analyst price targets
- **TextBlob:** News sentiment analysis

## Database

Analysis results are automatically saved to `stock_analysis.db` (SQLite).

**Schema:**
- `stocks` - Ticker symbols and company info
- `analyses` - Historical analysis snapshots with all indicators
- `news` - News articles with sentiment scores

**Query historical data:**
```python
from src.database import Database

db = Database()
with db.get_session() as session:
    # Your queries here
    pass
```

## Dependencies

Core libraries:
- `pandas` - Data manipulation
- `yfinance` - Yahoo Finance API wrapper
- `curl_cffi` - HTTP client with browser impersonation
- `beautifulsoup4` - HTML parsing for web scraping
- `streamlit` - Web dashboard framework
- `plotly` - Interactive charting
- `sqlalchemy` - Database ORM
- `textblob` - Sentiment analysis

See [`requirements.txt`](requirements.txt) for complete list.

## Project Structure

```
growth_invest_plan/
├── src/
│   ├── analyzer.py              # Main analysis facade
│   ├── dashboard.py             # Streamlit web app
│   ├── database.py              # Database connection
│   ├── models.py                # SQLAlchemy models
│   ├── formatter.py             # Console output formatting
│   ├── exporter.py              # CSV export
│   ├── visualization.py         # Static chart generator (mplfinance)
│   ├── visualization_plotly.py  # Interactive charts (Plotly)
│   └── data_sources/
│       ├── base.py              # Abstract base classes
│       ├── yfinance_source.py   # Technical data + indicators
│       ├── finviz_source.py     # Fundamental data
│       ├── marketbeat_source.py # Analyst targets
│       └── news_source.py       # News sentiment
├── tests/                       # Unit tests
├── charts/                      # Generated chart images
├── app.py                       # CLI entry point
├── stock_analysis.db            # SQLite database (auto-created)
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Development

### Running Tests
```bash
pytest
```

### With Coverage
```bash
pytest --cov=src --cov-report=html
```

### Code Style
The project follows PEP 8 guidelines with type hints throughout.

## Docker Support

Build and run with Docker:

```bash
# Build
docker build -t growth-invest-plan .

# Run CLI
docker run --rm growth-invest-plan AAPL

# Note: Dashboard mode not supported in Docker (requires browser)
```

## License

MIT

## Contributing

Contributions welcome! Please ensure:
- Type hints on all functions
- Unit tests for new features
- Documentation updates
