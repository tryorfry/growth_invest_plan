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

### User Story 3 - Interactive Deep-Dive (Priority: P1)
As a trader, I want to click on any stock in the report dashboard or email link and be taken to the full interactive analysis in a new tab without having to log in again.

**Acceptance Scenarios**:
1. **Given** a report dashboard view, **When** I click "Open Deep Dive", **Then** a new tab opens directly to that stock's analysis.
2. **Given** the new tab opens, **When** the session was previously authenticated, **Then** the new tab preserves that session using a secure signed token.

## Technical Implementation Notes
- **Report Engine**: `src/services/report_generator.py` processes batch analyses using `asyncio.gather`.
- **Export**: `src/services/export_service.py` handles Excel generation with multi-sheet sector organization.
- **Delivery**: `src/services/email_service.py` uses Gmail SMTP with SSL/TLS and App Passwords.
- **Persistence**: `AutomatedReport` table in `stock_analysis.db` stores history, status, and Excel file paths.
- **Deep Linking**: `src/utils.py` provides `render_deep_dive_button` which signs requests with `hash(username + password_hash)`.
- **Routing**: `src/dashboard.py` intercepts `auth_user`, `auth_token`, and `ticker` query parameters to automate login and page routing.
