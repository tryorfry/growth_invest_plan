# Implementation Plan: Automated Trading Reports

## Architecture
- **Backend**: `src/services/report_generator.py` coordinates data fetching for all tickers using existing UI functions to ensure DRY principle.
- **Delivery**: `src/services/export_service.py` formats to Excel/CSV. `src/services/email_service.py` sends via SMTP.
- **Automation**: `scripts/run_daily_reports.py` invoked by a background scheduler every 6 hours.
- **Dashboard**: `src/views/automated_reports.py` shows historical runs stored in the `AutomatedReports` DB table.

## Steps
1. Define database schema in `src/database.py`.
2. Implement data pipeline (`report_generator`).
3. Implement export and email delivery.
4. Implement UI Dashboard.
5. Setup the scheduler script.
