# Feature Specification: Automated Trading Reports

**Feature Branch**: `005-automated-trading-reports`
**Created**: 2026-04-25
**Status**: Draft

## User Scenarios

### User Story 1 - Daily Trading Reports (Priority: P1)
As a trader, I want to receive a daily automated report covering all my tracked stocks, evaluating them against the 9-point checklist, 3 trading styles (Growth, Swing, Trend), latest news catalysts, and earnings dates. This report should be emailed to me automatically every 6 hours as a spreadsheet.

**Acceptance Scenarios**:
1. **Given** the scheduler triggers every 6 hours, **When** the `report_generator` executes, **Then** an aggregated spreadsheet report is generated containing all required data columns.
2. **Given** a generated report, **When** the email service is invoked, **Then** the report is emailed successfully.

### User Story 2 - UI Dashboard & Historical Data (Priority: P2)
As a trader, I want to see a history of these automated reports within the Streamlit UI, so I can download past reports manually.

**Acceptance Scenarios**:
1. **Given** reports are stored in the database, **When** I navigate to the "Automated Reports" dashboard, **Then** I see a historical list of runs.
2. **Given** the list of runs, **When** I click "Download", **Then** the exact spreadsheet is provided to me.
