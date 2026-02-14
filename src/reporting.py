"""Reporting utility for exporting analysis data to Excel"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
import io

class ReportGenerator:
    """Generates professional Excel reports from stock analysis results"""
    
    @staticmethod
    def _clean_df_for_excel(df: pd.DataFrame) -> pd.DataFrame:
        """Strip timezones from all datetime columns and index for Excel compatibility"""
        df = df.copy()
        
        # Handle index
        if hasattr(df.index, 'tz') and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
            
        # Handle columns
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                if hasattr(df[col].dt, 'tz') and df[col].dt.tz is not None:
                    df[col] = df[col].dt.tz_localize(None)
        
        return df

    @staticmethod
    def generate_excel_report(analysis: Any, valuation_data: Dict[str, Any] = None) -> bytes:
        """
        Generate a multi-sheet Excel report in memory.
        """
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
            # 1. Summary Sheet
            summary_data = {
                'Metric': [
                    'Ticker', 'Company', 'Price', 
                    'Market Data Date', 'Analysis Time',
                    'Analyst Target', 'Analyst Source',
                    'DCF Intrinsic Value', 'Graham Number',
                    'News Sentiment'
                ],
                'Value': [
                    analysis.ticker,
                    analysis.company_name,
                    f"${analysis.current_price:.2f}",
                    analysis.timestamp.strftime('%Y-%m-%d') if hasattr(analysis.timestamp, 'strftime') else str(analysis.timestamp),
                    analysis.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(analysis.analysis_timestamp, 'strftime') else str(analysis.analysis_timestamp),
                    f"${analysis.median_price_target:.2f}" if analysis.median_price_target else "N/A",
                    analysis.analyst_source or "N/A",
                    f"${valuation_data.get('intrinsic_value'):.2f}" if valuation_data else "N/A",
                    "Calculated in Dashboard",
                    f"{analysis.news_sentiment:.2f}" if analysis.news_sentiment is not None else "N/A"
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # 2. Fundamentals Sheet
            if analysis.finviz_data:
                fundamental_metrics = []
                for k, v in analysis.finviz_data.items():
                    fundamental_metrics.append({'Metric': k, 'Value': v})
                pd.DataFrame(fundamental_metrics).to_excel(writer, sheet_name='Fundamentals', index=False)
            
            # 3. Technicals Sheet
            technical_data = {
                'Indicator': ['ATR', 'EMA20', 'EMA50', 'EMA200', 'RSI', 'MACD', 'Bollinger Upper', 'Bollinger Lower'],
                'Value': [
                    analysis.atr, analysis.ema20, analysis.ema50, analysis.ema200,
                    analysis.rsi, analysis.macd, analysis.bollinger_upper, analysis.bollinger_lower
                ]
            }
            pd.DataFrame(technical_data).to_excel(writer, sheet_name='Technicals', index=False)
            
            # 4. Historical Data
            if analysis.history is not None:
                hist_export = ReportGenerator._clean_df_for_excel(analysis.history)
                hist_export.to_excel(writer, sheet_name='Historical Data')
            
            # Formatting (optional but nice)
            workbook = writer.book
            for sheet in writer.sheets.values():
                sheet.set_column('A:B', 20)
                
        return buf.getvalue()
