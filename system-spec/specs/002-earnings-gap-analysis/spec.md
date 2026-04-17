# Feature Specification: Historical Earnings Gap Analysis

**Feature Branch**: `002-earnings-gap-analysis`  
**Created**: 2026-04-17  
**Status**: Draft  
**Input**: User description: "for every trading styles we already have the earning date displayed. Now I want to show the usual gapping that had happend in past may be take for at least 1 year data and show the projected gapping risk percentage."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Historical Earnings Insight (Priority: P1)

As a trader, I want to see how the stock price has reacted immediately following past earnings reports over the last year, so that I can anticipate the potential volatility and direction of the next report.

**Why this priority**: Earnings reactions are the single largest source of overnight risk. Providing context on past gaps helps traders decide whether to hold or hedge a position.

**Independent Test**: Can be verified by comparing the displayed historical gaps for a known ticker (e.g., TSLA) against a reliable financial data provider (e.g., Yahoo Finance).

**Acceptance Scenarios**:

1. **Given** a ticker with at least 4 past earnings reports, **When** I view the dashboard, **Then** I see the "Earnings Day Gap %" for the last 4 quarters (1 year).
2. **Given** a ticker with multiple earnings events, **When** calculating gaps, **Then** the system uses the price change between the close of the day before earnings and the open (or close) of the earnings day.

---

### User Story 2 - Projected Gap Risk Metrics (Priority: P2)

As a trader, I want to see a "Projected Gap Risk" calculated from historical behavior, so that I have a quantifiable metric for "Expected Move" when planning my position sizing before an earnings event.

**Why this priority**: Simple lists of numbers are hard to process quickly; an aggregated "Risk %" allows for immediate comparison across different stocks in a portfolio.

**Independent Test**: The "Projected Gap Risk" should accurately represent the average magnitude of past moves (Average Absolute Gap).

**Acceptance Scenarios**:

1. **Given** historical gap data, **When** viewing the Earnings section, **Then** I see a "Gap Risk %" expressing the average magnitude of the earnings move.
2. **Given** a stock with very high historical volatility (e.g., high-growth tech), **When** checking the risk, **Then** the Gap Risk % should reflect that higher historical variance compared to stable blue-chip stocks.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fetch historical earnings data for at least the last 4 quarters (1 year).
- **FR-002**: System MUST calculate the "Gap %" for each earnings event (Day-of-reaction percentage).
- **FR-003**: System MUST calculate a "Projected Gap Risk" metric based on the average absolute magnitude of historical moves.
- **FR-004**: Dashboard MUST display the historical gaps in a table or list format near the "Next Earnings" alert.
- **FR-005**: Dashboard MUST highlight the Projected Gap Risk as a primary metric when an earnings date is approaching (within warning threshold).

### Key Entities

- **Earnings Event**: A record containing the date, the price before the announcement, and the price reaction immediately following the announcement.
- **Gap Risk Percentage**: A calculated metric representing the expected magnitude of price movement (e.g., Mean Absolute Deviation of past earnings reactions).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view at least 4 quarters of historical earnings gap data on a single screen.
- **SC-002**: The Gap Risk metric is calculated and displayed within 2 seconds of the main analysis loading.
- **SC-003**: 100% of analyzed tickers (with historical data available) display a valid projected risk percentage.

## Assumptions

- We will use existing price data sources (e.g., Yahoo Finance) to derive gaps, as "Open" prices on earnings days are the standard measure for gaps.
- "Projected Gap Risk" will be calculated as the **Mean Absolute Gap** of the last 4-8 events to represent the "expected move" magnitude.
- The feature applies to all trading styles (Growth, Swing, Trend) because earnings risk is universal.
- Historical data availability depends on the data provider (yfinance). if less than 1 year is available, we show what is available.
