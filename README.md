# Growth Investment Plan Analysis Tool

A comprehensive stock analysis tool that combines technical indicators, fundamental data, and analyst sentiment to help evaluate growth investment opportunities.

## Features

### 📊 Technical Analysis
- **ATR (Average True Range):** 14-day volatility measurement
- **EMAs (Exponential Moving Averages):** 20, 50, and 200-period trend indicators
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
- **Valuation Ratios:** P/E, Forward P/E, PEG

### 📈 Financial Data (via yfinance)
- **Latest Quarterly Revenue**
- **Operating Income**
- **Basic EPS (Earnings Per Share)**
- **Next Earnings Date** with countdown
- **⚠️ Earnings Warning:** Alerts when earnings are less than 10 days away

### 🎯 Analyst Sentiment (via MarketBeat)
- **Median Price Target** from analyst ratings published after the most recent earnings announcement

## Prerequisites

- Python 3.8+
- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/) (optional, for containerized deployment)

## Installation

### Option 1: Local Python Environment

1.  Clone the repository:
    ```bash
    git clone https://github.com/tryorfry/growth_invest_plan.git
    cd growth_invest_plan
    ```

2.  Create a Virtual Environment:
    ```bash
    python -m venv .venv
    ```

3.  Activate the Virtual Environment:
    -   **Windows (PowerShell):**
        ```powershell
        .venv\Scripts\Activate.ps1
        ```
    -   **Windows (CMD):**
        ```cmd
        .venv\Scripts\activate.bat
        ```
    -   **Windows (Git Bash):**
        ```bash
        source .venv/Scripts/activate
        ```
    -   **macOS/Linux:**
        ```bash
        source .venv/bin/activate
        ```

4.  Install Dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Option 2: Docker

1.  Build the Docker image:
    ```bash
    docker build -t growth-invest-plan .
    ```

2.  Run the container:
    ```bash
    docker run --rm growth-invest-plan AAPL
    ```

## Usage

### Local Execution

```bash
python main.py [TICKER]
```

### Docker Execution

```bash
docker run --rm growth-invest-plan [TICKER]
```

### Examples

```bash
# Analyze Apple
python main.py AAPL

# Analyze NVIDIA
python main.py NVDA

# Analyze Google
python main.py GOOGL
```

## Sample Output

```
--- Analysis for NVDA (2026-02-11 00:00:00-05:00) ---
Current Price: 191.10
Open: 192.42 | High: 193.26 | Low: 188.77 | Close: 191.10
------------------------------
ATR (14):   6.89
EMA 20:     185.54
EMA 50:     185.02
EMA 200:    170.98
Last Earnings: 2025-11-19
Median MBP (Post-Earnings): $275.00

--- Finviz Data ---
Market Cap: 4648.83B
Analysts Recom: 1.35
Inst Own: 68.38%
Avg Volume: 180.68M
ROE: 107.36% | ROA: 77.15%
EPS Growth (This Y): 56.58%
EPS Growth (Next Y): 65.43%
EPS Growth (Next 5Y): 49.53%
P/E: 47.38 | Fwd P/E: 24.70 | PEG: 0.50

--- Fundamentals (Macrotrends Context) ---
Latest Revenue (Quarterly): $57.01B
Op Income (Quarterly): $36.01B
Basic EPS (Quarterly): 1.31
Next Earnings Date: 2026-02-26 (13 days left)
```

## Data Sources

- **yfinance:** Historical price data, technical indicators, financial statements, earnings dates
- **Finviz:** Fundamental metrics, analyst recommendations, growth projections
- **MarketBeat:** Post-earnings analyst price targets

## Dependencies

- `pandas` - Data manipulation
- `yfinance` - Yahoo Finance API wrapper
- `curl_cffi` - HTTP client with browser impersonation (bypasses bot protection)
- `beautifulsoup4` - HTML parsing for web scraping
- `lxml` - XML/HTML parser

## License

MIT
