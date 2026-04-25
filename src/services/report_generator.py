import asyncio
from typing import List, Dict, Any
import datetime

from src.database import Database
from src.analyzer import StockAnalyzer
from src.logic.scorer import ChecklistScorer

async def generate_reports(tickers: List[str] = None) -> List[Dict[str, Any]]:
    """
    Generates trading reports for the given list of tickers.
    If no tickers are provided, it fetches all tickers from the database.
    """
    db = Database()
    if not tickers:
        tickers = db.get_all_tickers()
    
    analyzer = StockAnalyzer()
    reports = []
    
    print(f"Generating reports for {len(tickers)} tickers...")
    
    for ticker in tickers:
        print(f"Processing {ticker}...")
        try:
            # We use multi_analyze to get all 3 trading styles
            analysis = await analyzer.multi_analyze(ticker, verbose=False, force_refresh=True)
            if not analysis:
                print(f"Failed to analyze {ticker}")
                continue
                
            # 9-point Checklist Score
            score, total, details = ChecklistScorer.calculate_score(analysis)
            
            # Format the output strictly matching UI data to preserve DRY
            report_data = {
                "Ticker": ticker,
                "Company": getattr(analysis, 'company_name', 'N/A'),
                "Sector": getattr(analysis, 'sector', 'N/A'),
                "Industry": getattr(analysis, 'industry', 'N/A'),
                "Current Price": analysis.current_price,
                "Checklist Score": f"{score}/{total}",
                
                # Trading Styles Data
                "Growth Score": analysis.style_results.get('Growth Investing', {}).get('score', 0),
                "Growth Trend": analysis.style_results.get('Growth Investing', {}).get('trend', 'N/A'),
                "Swing Score": analysis.style_results.get('Swing Trading', {}).get('score', 0),
                "Swing Trend": analysis.style_results.get('Swing Trading', {}).get('trend', 'N/A'),
                "Trend Score": analysis.style_results.get('Trend Trading', {}).get('score', 0),
                "Trend Trend": analysis.style_results.get('Trend Trading', {}).get('trend', 'N/A'),
                "Best Style": analysis.best_style,
                
                # Setup details (based on best style)
                "Suggested Entry": getattr(analysis, 'suggested_entry', 'N/A'),
                "Stop Loss": getattr(analysis, 'suggested_stop_loss', 'N/A'),
                "Target Price": getattr(analysis, 'target_price', 'N/A'),
                "R/R": getattr(analysis, 'reward_to_risk', 'N/A'),
                
                # Earnings & News
                "Next Earnings": str(analysis.next_earnings_date.date()) if getattr(analysis, 'next_earnings_date', None) else "N/A",
                "Days Until Earnings": getattr(analysis, 'days_until_earnings', 'N/A'),
                "News Sentiment": getattr(analysis, 'news_summary', 'N/A'),
                "Sentiment Score": getattr(analysis, 'news_sentiment', 'N/A'),
                
                # Analyst
                "Median Target": getattr(analysis, 'median_price_target', 'N/A'),
                "Analyst Source": getattr(analysis, 'analyst_source', 'N/A'),
                "Recent Action": getattr(analysis, 'marketbeat_action_recent', 'N/A')
            }
            
            reports.append(report_data)
            
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            
    return reports
