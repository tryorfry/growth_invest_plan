# Growth Investment Analyzer - System Architecture

This document maps out the core architecture and data flow of the Growth Investment Analyzer platform.

## Architecture Flowchart

```mermaid
graph TD
    %% User Interfaces
    Client[Web Browser] -->|HTTP/WebSockets| StreamlitApp

    subgraph Docker Container
        StreamlitApp[Streamlit Server <br/> :8501]

        %% Authentication Gate
        subgraph Security Layer
            StreamlitApp --> AuthGate{AuthManager <br/> Session State}
            AuthGate -->|Unauthenticated| LoginPage[Login / Signup UI]
            AuthGate -->|Authenticated| Dashboard[Full Dashboard UI]
            AuthGate -->|Authenticated| SubPages[Portfolio / Watchlist UI]
        end

        %% Internal Python Modules
        subgraph Core Engines
            Dashboard --> Analyzer[StockAnalyzer Engine]
            Dashboard --> Scheduler[Background Scheduler Thread]
            Scheduler --> AlertsEngine[Alerts Processing Engine]
            SubPages --> PortfolioManager[Portfolio Manager]
            PortfolioManager --> PositionSizer[Position Sizer & Risk Math]
        end

        %% Data Sources Layer
        subgraph External Data Extraction
            Analyzer --> YFinance[YFinance Source <br/> Price/Volume/Earnings Date]
            Analyzer --> Finviz[Finviz Source <br/> Fundamentals/Valuation]
            Analyzer --> MarketBeat[MarketBeat Source <br/> Analyst Targets]
            Analyzer --> NewsSource[News Sentiment Source <br/> TextBlob NLP]
            Analyzer --> SectorSource[Sector Rotation Source <br/> ETF Relative Strength]
        end

        %% Advanced Mathematical Modeling
        subgraph Quantitative Models
            Analyzer --> MonteCarlo[Monte Carlo Engine <br/> Geometric Brownian Motion]
            Analyzer --> SupportResistance[Support/Resistance Math <br/> Volume Profile & Clustering]
        end

        %% Database Persistence
        subgraph Local Database Storage
            Database[(SQLite: stock_analysis.db)]
            AuthGate <-->|User Records & Password Hashes| Database
            Analyzer -->|Save Snapshot| Database
            AlertsEngine <-->|Read Triggers & History| Database
            Dashboard <-->|Portfolios & Watchlists| Database
        end
    end
```

### Key Components:
1. **Security Layer:** Using `bcrypt` and Streamlit `session_state`, the application forcefully routes unauthenticated web traffic to the Login screen, securing the entire local SQL database.
2. **Core Engines:** The `StockAnalyzer` class coordinates multiple asynchronous data fetches, while the Background Scheduler runs in a separate thread to evaluate user-defined price alerts continuously.
3. **External Data Extraction:** A highly extensible scraper implementation (`DataSource` abstract class) fetches data from Yahoo Finance, Finviz, and MarketBeat cleanly.
4. **Quantitative Models:** The system runs mathematical models locally using `numpy` and `pandas` (such as the Monte Carlo simulation and 1D price clustering algorithms for support/resistance).
5. **Database Persistence:** Everything relies on a consolidated local SQLAlchemy database (`stock_analysis.db`), preserving user privacy and circumventing expensive structured API subscription costs.
6. **Risk Management:** The new `PortfolioManager` tracks Available Cash properly and dynamically calculates Net Liquidation Value (NLV), while the `PositionSizer` enforces 1% trade risk metrics across the portfolio.
