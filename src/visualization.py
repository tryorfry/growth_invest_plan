
import os
import mplfinance as mpf
import pandas as pd
from typing import Optional
from .analyzer import StockAnalysis

class ChartGenerator:
    """Generates technical analysis charts"""
    
    def __init__(self, output_dir: str = "charts"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
    def generate_chart(self, analysis: StockAnalysis) -> Optional[str]:
        """
        Generate a candlestick chart with technical indicators.
        
        Args:
            analysis: StockAnalysis object containing historical data
            
        Returns:
            Path to the saved image file or None if failed
        """
        if analysis.history is None or analysis.history.empty:
            print(f"No historical data available for chart: {analysis.ticker}")
            return None
            
        try:
            # Prepare data
            df = analysis.history.copy()
            
            # Create plots for EMAs
            plots = []
            
            if 'EMA20' in df.columns:
                plots.append(mpf.make_addplot(df['EMA20'], color='red', width=1.0))
            if 'EMA50' in df.columns:
                plots.append(mpf.make_addplot(df['EMA50'], color='green', width=1.0))
            if 'EMA200' in df.columns:
                plots.append(mpf.make_addplot(df['EMA200'], color='purple', width=1.5))
                
            # Add Median Price Target line if available
            if analysis.median_price_target:
                target_line = [analysis.median_price_target] * len(df)
                plots.append(mpf.make_addplot(target_line, color='green', linestyle='dashed', width=1.0))

            output_file = os.path.join(self.output_dir, f"{analysis.ticker}_chart.png")
            
            # Plot
            mpf.plot(
                df,
                type='candle',
                style='yahoo',
                title=f"{analysis.ticker} Technical Analysis",
                ylabel='Price ($)',
                addplot=plots,
                volume=True,
                savefig=dict(fname=output_file, dpi=100, bbox_inches='tight')
            )
            
            return output_file
            
        except Exception as e:
            print(f"Error generating chart for {analysis.ticker}: {e}")
            return None
