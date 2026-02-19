
import schedule
import time
import asyncio
import logging
from datetime import datetime
from sqlalchemy import select
from src.database import Database
from src.models import Stock
from src.analyzer import StockAnalyzer
from src.alerts.alert_engine import AlertEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_all_tickers():
    """Fetch all unique tickers from the database"""
    db = Database()
    with db.get_session() as session:
        result = session.execute(select(Stock.ticker))
        tickers = [row[0] for row in result.fetchall()]
    return tickers

async def analyze_ticker(analyzer, alert_engine, ticker):
    """Analyze a single ticker and check alerts"""
    try:
        logger.info(f"Analyzing {ticker}...")
        analysis = await analyzer.analyze(ticker)
        
        if analysis:
            logger.info(f"Successfully analyzed {ticker}")
            
            # Check alerts
            db = Database()
            with db.get_session() as session:
                triggered = alert_engine.check_alerts(session, analysis)
                if triggered:
                    logger.info(f"Triggered {len(triggered)} alerts for {ticker}")
        else:
            logger.warning(f"Analysis failed for {ticker} (no data returned)")
            
    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {e}")

async def run_analysis_cycle():
    """Run analysis for all stocks in the database"""
    logger.info("Starting hourly analysis cycle...")
    
    tickers = get_all_tickers()
    if not tickers:
        logger.warning("No stocks found in database to analyze.")
        return

    logger.info(f"Found {len(tickers)} stocks to analyze: {', '.join(tickers)}")
    
    analyzer = StockAnalyzer()
    alert_engine = AlertEngine() # Initialize alert engine
    
    # Process sequentially to avoid rate limits and database locks
    for ticker in tickers:
        await analyze_ticker(analyzer, alert_engine, ticker)
        # Small delay between requests to be polite to APIs
        await asyncio.sleep(2)
        
    logger.info("Hourly analysis cycle completed.")

def job():
    """Wrapper to run the async analysis cycle"""
    try:
        asyncio.run(run_analysis_cycle())
    except Exception as e:
        logger.error(f"Job execution failed: {e}")

def main():
    logger.info("Scheduler started. Running hourly stock analysis.")
    
    # Schedule the job to run every hour
    schedule.every(1).hours.do(job)
    
    # Run immediately on startup
    logger.info("Running initial analysis...")
    try:
        job()
    except Exception as e:
        logger.error(f"Initial analysis failed: {e}")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except Exception as e:
            logger.error(f"Scheduler crashed in main loop: {e}")
            time.sleep(60) # Prevent tight loop if persistent error occurs

def start_scheduler_thread():
    """Start the scheduler in a background thread"""
    import threading
    
    # Check if already running to prevent duplicates
    for thread in threading.enumerate():
        if thread.name == "SchedulerThread":
            logger.info("Scheduler thread already running.")
            return

    logger.info("Starting scheduler background thread...")
    t = threading.Thread(target=main, name="SchedulerThread", daemon=True)
    t.start()

if __name__ == "__main__":
    main()
