
import pandas as pd
from typing import List
from .analyzer import StockAnalysis

def export_to_csv(analyses: List[StockAnalysis], filename: str = "analysis_results.csv"):
    """
    Export a list of StockAnalysis objects to a CSV file.
    """
    if not analyses:
        print("No analysis results to export.")
        return

    data = []
    for a in analyses:
        row = {
            "Ticker": a.ticker,
            "Price": a.current_price,
            "Target Price": a.median_price_target,
            "Upside": ((a.median_price_target - a.current_price) / a.current_price * 100) if a.median_price_target and a.current_price else None,
            "Earnings Warning": "YES" if a.has_earnings_warning() else "No",
            "News Sentiment": a.news_sentiment,
            "News Summary": a.news_summary,
            "Market Cap": a.finviz_data.get("Market Cap"),
            "P/E": a.finviz_data.get("P/E"),
            "Forward P/E": a.finviz_data.get("Forward P/E"),
            "PEG": a.finviz_data.get("PEG"),
            "EPS Growth (Next 5Y)": a.finviz_data.get("EPS next 5Y"),
            "Revenue": a.revenue,
            "Operating Income": a.operating_income,
             "Basic EPS": a.basic_eps
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Results exported to {filename}")
