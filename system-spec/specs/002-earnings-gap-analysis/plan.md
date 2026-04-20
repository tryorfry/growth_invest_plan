# Implementation Plan: Historical Earnings Gap Analysis

**Branch**: `002-earnings-gap-analysis` | **Date**: 2026-04-17 | **Spec**: [spec.md](./spec.md)

## Summary
Add a historical analysis layer to the dashboard that quantifies overnight earnings risk. This involves fetching past earnings dates from Yahoo Finance, calculating the day-of-reaction price gap, and presenting an aggregated "Gap Risk %" to the user.

## Technical Context
- **Primary Dependencies**: `yfinance`, `curl_cffi`, `pandas`
- **Storage**: `sqlite` (SQLAlchemy)
- **Model Fields**: `earnings_history_json` (Text), `projected_gap_risk` (Float)

## Project Structure

### Documentation
```text
system-spec/specs/002-earnings-gap-analysis/
├── spec.md
├── research.md
├── plan.md              # This file
└── tasks.md
```

### Source Code
- `src/models.py`: Added `earnings_history_json` and `projected_gap_risk` to `Analysis`.
- `src/data_sources/earnings_source.py`: New source class for post-earnings analysis.
- `src/analyzer.py`: Integration into the main `analyze` flow with cache-aside support.
- `src/components/earnings.py`: UI component for rendering the gap table and risk metrics.

## Tasks
1. [x] Update database schema (`Analysis` model).
2. [x] Create `EarningsSource` with multi-attempt fallback (JSON -> API -> Scraping).
3. [x] Implement gap calculation logic in `StockAnalyzer`.
4. [x] Create Streamlit component for earnings visualization.
5. [x] Harden SSL handling for Yahoo Finance requests.
