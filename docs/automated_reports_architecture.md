# Automated Trading Reports Architecture

## Overview
The Automated Trading Reports subsystem is designed to run completely decoupled from the interactive Streamlit dashboard while guaranteeing 100% data parity. It achieves this by employing a DRY (Don't Repeat Yourself) architecture where both the background scheduler and the UI rely on the identical `StockAnalyzer` and `ChecklistScorer` core engines.

## Architecture Diagram

```mermaid
sequenceDiagram
    participant S as scheduler.py (Cron)
    participant R as run_daily_reports.py
    participant DB as SQLite / DB
    participant A as StockAnalyzer (Engine)
    participant TS as SectorTickerScraper
    participant UI as Streamlit UI

    %% Workflow Step 1: Trigger
    S->>R: Spawns process (Every 6 Hours)
    
    %% Workflow Step 2: Init DB
    R->>DB: Create "AutomatedReport" record (Status: 'running')
    
    %% Workflow Step 3: Resolution
    R->>TS: Fetch Tickers (Watchlist or SP500 Golden List)
    TS-->>R: Ticker list
    
    %% Workflow Step 4: Analysis Loop
    loop For each Ticker
        R->>A: analyze(ticker)
        A-->>R: Analysis JSON (9-Point, Styles)
        R->>DB: Update `progress_pct` & `current_ticker`
    end
    
    %% Workflow Step 5: Export & Delivery
    R->>R: Export to Excel .xlsx (Grouped by Sector)
    R->>R: Send via SMTP Email
    
    %% Workflow Step 6: Finalize DB
    R->>DB: Update Record (Status: 'completed', save JSON payload)

    %% User Interaction
    UI->>DB: Fetch Report History
    UI-->>UI: Render Interactive Plotly Charts & DataFrame
```

## Data Fallbacks & Robustness
The system implements a unified `SP500_GOLDEN_LIST` from the `SectorTickerScraper`. When the Yahoo Finance API aggressively rate limits and drops `sector` or `company_name` via `fast_info`, the report generator relies on this golden mapping to ensure charting layers (like the Plotly Sector breakdown) never fail.
