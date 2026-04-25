import time
import subprocess
import os
from datetime import datetime

def run_script():
    print(f"[{datetime.now()}] Executing run_daily_reports.py...")
    script_path = os.path.join(os.path.dirname(__file__), "run_daily_reports.py")
    subprocess.run(["python", script_path])

if __name__ == "__main__":
    interval_hours = 6
    interval_seconds = interval_hours * 3600
    
    print(f"Starting Report Scheduler. Will run every {interval_hours} hours.")
    
    while True:
        run_script()
        print(f"[{datetime.now()}] Sleeping for {interval_hours} hours...")
        time.sleep(interval_seconds)
