# Growth Investment Plan Analysis Tool

This project fetches stock data, calculates technical indicators (ATR, EMA), and retrieves analyst ratings from MarketBeat to determine the Maximum Buy Price (MBP).

## Prerequisites

- Python 3.8+
- [Git](https://git-scm.com/)

## Installation

1.  Clone the repository (if you haven't already):
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
    -   **macOS/Linux:**
        ```bash
        source .venv/bin/activate
        ```

4.  Install Dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the main script with a stock ticker symbol:

```bash
python main.py [TICKER]
```

Example:

```bash
python main.py AAPL
python main.py NVDA
```

## Features

-   **ATR (Average True Range):** 14-day calculation.
-   **EMA (Exponential Moving Average):** 20, 50, and 200 periods.
-   **MarketBeat Integration:** Scrapes analyst ratings to find the median Maximum Buy Price post-earnings.
-   **Earnings Date:** Fetches the latest earnings date via yfinance.

## License

MIT
