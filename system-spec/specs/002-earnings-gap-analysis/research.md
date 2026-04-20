# Research: Historical Earnings Gap Analysis

## Goal
Quantify the "Expected Move" (gap risk) for a ticker based on its historical reactions to earnings reports.

## Methodology
1. **Data Source**: Use Yahoo Finance (`yfinance` or direct JSON endpoint) to fetch historical earnings dates.
2. **Price Extraction**: Identify the close price of the trading day *before* the earnings date (T-1) and the open/close prices of the earnings reaction day (T0).
3. **Gap Calculation**: `Gap % = ((T0_Price - T-1_Price) / T-1_Price) * 100`.
4. **Risk Metric**: Calculate the **Mean Absolute Gap** (MAG) of the last 4-8 earnings events to represent the projected risk.
    - `MAG = Sum(abs(Gap_i)) / N`

## Findings
- **TSLA Example**: Historically shows gaps ranging from 2% to 12%. The MAG provides a more stable expectation than just the last gap.
- **Timing Nulls**: Earnings sometimes happen on non-trading days. Fallback logic must find the nearest following trading day index.
- **SSL Issues**: Yahoo Finance frequently blocks/throttles scraping; hardened `DataSource` with `curl_cffi` and `verify=False` fallback is required for reliability.

## Implementation Details
- **Persistence**: Store the serialized history in `Analysis.earnings_history_json` and the summary risk in `Analysis.projected_gap_risk`.
- **UI**: Display as a collapsed expander in the technical section to avoid cluttering the primary metrics.
