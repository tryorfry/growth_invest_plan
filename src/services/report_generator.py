import asyncio
from typing import List, Dict, Any
import datetime

from src.database import Database
from src.analyzer import StockAnalyzer
from src.logic.scorer import ChecklistScorer

from src.data_sources.ticker_scraper import SectorTickerScraper

def get_golden_mapping() -> Dict[str, Dict[str, str]]:
    mapping = {}
    for sector, items in SectorTickerScraper.SP500_GOLDEN_LIST.items():
        for ticker, company in items:
            mapping[ticker] = {"Company": company, "Sector": sector}
    return mapping

async def generate_reports(tickers: List[str] = None, report_record_id: int = None, db_session = None) -> List[Dict[str, Any]]:
    """
    Generates trading reports for the given list of tickers.
    If no tickers are provided, it fetches all tickers from the database.
    """
    db = Database()
    if not tickers:
        tickers = db.get_all_tickers()
    
    analyzer = StockAnalyzer()
    reports = []
    golden_mapping = get_golden_mapping()
    
    print(f"Generating reports for {len(tickers)} tickers...")
    
    for i, ticker in enumerate(tickers):
        print(f"Processing {ticker} ({i+1}/{len(tickers)})...")
        
        # Real-time progress update
        if report_record_id and db_session:
            try:
                from src.models import AutomatedReport
                report = db_session.query(AutomatedReport).get(report_record_id)
                if report:
                    report.current_ticker = ticker
                    report.progress_pct = int((i / len(tickers)) * 100)
                    db_session.commit()
            except Exception as e:
                print(f"Failed to update progress: {e}")
                
        try:
            # We use multi_analyze to get all 3 trading styles
            analysis = await analyzer.multi_analyze(ticker, verbose=False, force_refresh=True)
            if not analysis:
                print(f"Failed to analyze {ticker}")
                continue
                
            # 9-point Checklist Score
            score, total, details = ChecklistScorer.calculate_score(analysis)
            
            c_name = getattr(analysis, 'company_name', None)
            sector = getattr(analysis, 'sector', None)
            
            # Apply robust fallback for missing data using the DRY Golden List
            if ticker in golden_mapping:
                if not c_name or c_name == 'N/A' or c_name == ticker:
                    c_name = golden_mapping[ticker]["Company"]
                if not sector or sector == 'N/A':
                    sector = golden_mapping[ticker]["Sector"]
            else:
                c_name = c_name or 'N/A'
                sector = sector or 'N/A'
            
            # AI Conviction Summary
            ai_summary = "N/A"
            try:
                from src.ai_analyzer import AIAnalyzer
                ai = AIAnalyzer()
                if ai.is_available():
                    conviction_data = {
                        "trading_style": analysis.best_style,
                        "reward_to_risk": getattr(analysis, 'reward_to_risk', 'N/A'),
                        "atr_daily": getattr(analysis, 'atr_daily', getattr(analysis, 'atr', 'N/A')),
                        "earnings_deviation": getattr(analysis, 'expected_earnings_deviation_pct', 'N/A'),
                        "inst_own": analysis.finviz_data.get('Inst Own', 'N/A'),
                        "inst_trans": analysis.finviz_data.get('Inst Trans', 'N/A'),
                        "insider_own": analysis.finviz_data.get('Insider Own', 'N/A'),
                        "insider_trans": analysis.finviz_data.get('Insider Trans', 'N/A'),
                        "analyst_action": getattr(analysis, 'marketbeat_action_recent', getattr(analysis, 'recent_action', 'N/A')),
                        "news_sentiment_label": getattr(analysis, 'news_summary', 'Neutral'),
                        "news_score": getattr(analysis, 'news_sentiment', 0.0)
                    }
                    ai_summary = ai.generate_conviction_summary(ticker, conviction_data)
            except Exception as ai_e:
                print(f"Error generating AI conviction for {ticker}: {ai_e}")

            # Format the output strictly matching UI data to preserve DRY
            report_data = {
                "Ticker": ticker,
                "Company": c_name,
                "Sector": sector,
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
                "Risk Per Unit": getattr(analysis, 'risk_per_unit', 'N/A'),
                "Position Size (Units)": getattr(analysis, 'position_size_units', 'N/A'),
                "ATR": getattr(analysis, 'atr_daily', getattr(analysis, 'atr', 'N/A')),
                "Weekly ATR": getattr(analysis, 'atr', 'N/A'),
                "Checklist Details": details,
                
                # Earnings & News
                "Next Earnings": str(analysis.next_earnings_date.date()) if getattr(analysis, 'next_earnings_date', None) else "N/A",
                "Days Until Earnings": getattr(analysis, 'days_until_earnings', 'N/A'),
                "Expected Earnings Deviation": getattr(analysis, 'expected_earnings_deviation_pct', 'N/A'),
                "News Sentiment": getattr(analysis, 'news_summary', 'N/A'),
                "Sentiment Score": getattr(analysis, 'news_sentiment', 'N/A'),
                
                # Analyst
                "Median Target": getattr(analysis, 'median_price_target', 'N/A'),
                "Analyst Source": getattr(analysis, 'analyst_source', 'N/A'),
                "Recent Action": getattr(analysis, 'marketbeat_action_recent', getattr(analysis, 'recent_action', 'N/A')),
                
                # Flow Data
                "Inst Own": analysis.finviz_data.get('Inst Own', 'N/A'),
                "Inst Trans": analysis.finviz_data.get('Inst Trans', 'N/A'),
                "Insider Own": analysis.finviz_data.get('Insider Own', 'N/A'),
                "Insider Trans": analysis.finviz_data.get('Insider Trans', 'N/A'),
                
                # AI Conviction
                "AI Conviction Summary": ai_summary
            }
            
            reports.append(report_data)
            
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            
    return reports
