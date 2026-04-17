# Feature Specification: System Modernization & Refactoring

**Feature Branch**: `003-system-modernization`  
**Created**: 2026-04-17  
**Status**: Draft  
**Inputs**: All 4 technical debt candidates (Modularization, Robustness, Persistence, Standardization).

## Summary

This feature targets core architectural improvements to ensure the Growth Investment Analyzer remains maintainable and stable as it scales. We are moving from a monolithic dashboard to a modular component architecture, hardening our data acquisition layer against network/SSL failures, and optimizing the data lifecycle with a persistence-first cache-aside strategy.

## User Scenarios & Testing

### User Story 1 - Maintainable Architecture (Priority: P1)
As a developer, I want the dashboard logic to be broken into manageable modules so that I can add new UI features without navigating a 1,200+ line file.

**Goal**: Extract checklist, earnings analysis, and sidebar rendering into independent modules.

---

### User Story 2 - Resilient Data Scraping (Priority: P1)
As a user, I want the analysis to succeed even if a data provider has intermittent SSL or connectivity issues, so that I don't see "Failed to analyze" errors during market volatility.

**Goal**: Implement an SSL-fallback and retry mechanism in the base data source layer.

---

### User Story 3 - Optimized Data Performance (Priority: P2)
As a user, I want the dashboard to load instantly if I just viewed a ticker recently, so that the app feels fast and responsive.

**Goal**: Implement a "Cache-Aside" logic that prioritizes DB records within a defined TTL (Time-to-Live).

---

## Requirements

### Functional Requirements
- **FR-001**: System MUST modularize `src/dashboard.py` by extracting UI components into `src/components/`.
- **FR-002**: System MUST provide a unified HTTP request helper in `src/data_sources/base.py` with SSL-fallback support.
- **FR-003**: System MUST update the `Analysis` model to persist the "Earnings Gap Analysis" data fields.
- **FR-004**: System MUST implement a TTL check (default 24h) before fetching fresh analysis from external sources.
- **FR-005**: System MUST implement a global `AppError` class for standardized exception handling.

### Cache-Aside Logic (Task 3)
1.  Check for latest `Analysis` in the database for the given ticker.
2.  **Logic**: 
    - If `analysis.timestamp` is within the last 24 hours: Return DB record.
    - If `analysis.timestamp` is older than 24 hours: Trigger fresh fetch.
    - **Exception**: If user explicitly requests a "Refresh", or if data is missing in the DB record (e.g., NULL fields for new metrics), force a fetch.

---

## Success Criteria
- **SC-001**: `src/dashboard.py` is reduced by at least 40% in line count.
- **SC-002**: Data sources gracefully handle SSL certification errors (tested via manual SSL-fail simulation).
- **SC-003**: Repeat analyses of the same ticker (within TTL) load in <500ms by bypassing network calls.
- **SC-004**: All analyzed tickers record activity consistently in the `user_activity` table.
