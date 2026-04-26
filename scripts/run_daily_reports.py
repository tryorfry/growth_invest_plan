import sys
import os
import asyncio
import json
import traceback
from datetime import datetime

# Add the project root to the python path to allow importing src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.report_generator import generate_reports
from src.services.export_service import export_reports_to_excel
from src.services.email_service import send_report_email
from src.database import Database
from src.models import AutomatedReport

async def run_report(to_email: str = None, tickers: list = None):
    print(f"[{datetime.now()}] Starting Automated Report Generation...")
    db = Database()
    
    # Initialize DB record
    session = db.SessionLocal()
    report_record = AutomatedReport(status='running')
    session.add(report_record)
    session.commit()
    
    try:
        reports = await generate_reports(tickers=tickers, report_record_id=report_record.id, db_session=session)
        
        if not reports:
            print("No reports generated. Exiting.")
            report_record.status = 'failed'
            report_record.error_log = "No reports generated."
            session.commit()
            return
            
        print(f"Generated {len(reports)} reports. Exporting to Excel...")
        excel_path = export_reports_to_excel(reports)
        
        # Save to DB
        report_record.total_stocks_analyzed = len(reports)
        report_record.file_path = excel_path
        report_record.report_data_json = json.dumps(reports)
        report_record.status = 'completed'
        session.commit()
        
        if to_email:
            print(f"Sending email to {to_email}...")
            send_report_email(excel_path, to_email)
            
        print(f"[{datetime.now()}] Automated Report Run Completed Successfully.")
        
        # Clean up old data and files (older than 14 days)
        purge_old_reports(session)
        
    except Exception as e:
        error_msg = f"Error during report run: {e}\n{traceback.format_exc()}"
        print(error_msg)
        report_record.status = 'failed'
        report_record.error_log = error_msg
        session.commit()
    finally:
        session.close()

def purge_old_reports(session):
    from datetime import timedelta
    from src.models import AutomatedReport
    
    cutoff = datetime.utcnow() - timedelta(days=14)
    old_reports = session.query(AutomatedReport).filter(AutomatedReport.report_date < cutoff).all()
    
    if old_reports:
        count = len(old_reports)
        for r in old_reports:
            # Also clean up the actual Excel files if they exist
            if r.file_path and os.path.exists(r.file_path):
                try:
                    os.remove(r.file_path)
                except Exception as e:
                    print(f"Failed to delete old Excel file {r.file_path}: {e}")
            session.delete(r)
        session.commit()
        print(f"[{datetime.now()}] Purged {count} reports older than 14 days.")

if __name__ == "__main__":
    # Ensure it only goes to the Admin for now
    from src.database import Database
    from src.models import User
    
    db = Database()
    with db.get_session() as session:
        admin_user = session.query(User).filter(User.tier == 'admin').first()
        email = admin_user.email if admin_user else "sachindangol@gmail.com"
        
    asyncio.run(run_report(to_email=email))
