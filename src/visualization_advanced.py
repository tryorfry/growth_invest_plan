"""Advanced visualization components for comparison, heatmaps, and patterns"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from src.analyzer import StockAnalysis


class AdvancedVisualizations:
    """Generate advanced charts for stock analysis"""
    
    def create_comparison_chart(self, analyses: List[StockAnalysis], normalize: bool = True) -> go.Figure:
        """
        Create a multi-stock comparison chart.
        
        Args:
            analyses: List of StockAnalysis objects
            normalize: If True, normalize prices to 100 at start
            
        Returns:
            Plotly Figure with comparison chart
        """
        fig = go.Figure()
        
        for analysis in analyses:
            if analysis.history is None or analysis.history.empty:
                continue
            
            df = analysis.history.copy()
            prices = df['Close']
            
            if normalize:
                # Normalize to 100 at start
                prices = (prices / prices.iloc[0]) * 100
                y_label = "Normalized Price (Base=100)"
            else:
                y_label = "Price ($)"
            
            fig.add_trace(go.Scatter(
                x=df.index,
                y=prices,
                name=analysis.ticker,
                mode='lines',
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title="Stock Price Comparison",
            xaxis_title="Date",
            yaxis_title=y_label,
            hovermode='x unified',
            template='plotly_white',
            height=600
        )
        
        return fig
    
    def create_correlation_heatmap(self, analyses: List[StockAnalysis]) -> Optional[go.Figure]:
        """
        Create a correlation matrix heatmap.
        
        Args:
            analyses: List of StockAnalysis objects
            
        Returns:
            Plotly Figure with correlation heatmap
        """
        # Build dataframe with all stock prices
        price_data = {}
        
        for analysis in analyses:
            if analysis.history is None or analysis.history.empty:
                continue
            price_data[analysis.ticker] = analysis.history['Close']
        
        if len(price_data) < 2:
            return None
        
        df = pd.DataFrame(price_data)
        
        # Calculate correlation matrix
        corr_matrix = df.corr()
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale='RdBu',
            zmid=0,
            text=corr_matrix.values,
            texttemplate='%{text:.2f}',
            textfont={"size": 10},
            colorbar=dict(title="Correlation")
        ))
        
        fig.update_layout(
            title="Stock Price Correlation Matrix",
            template='plotly_white',
            height=600,
            width=700
        )
        
        return fig
    
    def create_performance_table(self, analyses: List[StockAnalysis]) -> pd.DataFrame:
        """
        Create a performance comparison table.
        
        Args:
            analyses: List of StockAnalysis objects
            
        Returns:
            DataFrame with performance metrics
        """
        data = []
        
        for analysis in analyses:
            if analysis.history is None or analysis.history.empty:
                continue
            
            df = analysis.history
            current_price = analysis.current_price
            
            # Calculate returns
            returns_1d = ((current_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2] * 100) if len(df) > 1 else 0
            returns_1w = ((current_price - df['Close'].iloc[-5]) / df['Close'].iloc[-5] * 100) if len(df) > 5 else 0
            returns_1m = ((current_price - df['Close'].iloc[-21]) / df['Close'].iloc[-21] * 100) if len(df) > 21 else 0
            returns_3m = ((current_price - df['Close'].iloc[-63]) / df['Close'].iloc[-63] * 100) if len(df) > 63 else 0
            
            # Volatility (standard deviation of returns)
            daily_returns = df['Close'].pct_change()
            volatility = daily_returns.std() * np.sqrt(252) * 100  # Annualized
            
            data.append({
                'Ticker': analysis.ticker,
                'Price': f"${current_price:.2f}",
                '1D %': f"{returns_1d:+.2f}%",
                '1W %': f"{returns_1w:+.2f}%",
                '1M %': f"{returns_1m:+.2f}%",
                '3M %': f"{returns_3m:+.2f}%",
                'Volatility': f"{volatility:.1f}%",
                'RSI': f"{analysis.rsi:.1f}" if analysis.rsi else "N/A",
                'P/E': analysis.finviz_data.get('P/E', 'N/A')
            })
        
        return pd.DataFrame(data)
    
    def create_sector_heatmap(self, analyses: List[StockAnalysis]) -> Optional[go.Figure]:
        """
        Create a sector performance heatmap.
        
        Args:
            analyses: List of StockAnalysis objects
            
        Returns:
            Plotly Figure with sector heatmap
        """
        # Group by sector and calculate average performance
        sector_data = {}
        
        for analysis in analyses:
            if not analysis.sector or analysis.history is None or analysis.history.empty:
                continue
            
            df = analysis.history
            current_price = analysis.current_price
            
            # Calculate 1-month return
            returns_1m = ((current_price - df['Close'].iloc[-21]) / df['Close'].iloc[-21] * 100) if len(df) > 21 else 0
            
            if analysis.sector not in sector_data:
                sector_data[analysis.sector] = []
            sector_data[analysis.sector].append(returns_1m)
        
        if not sector_data:
            return None
        
        # Calculate average returns per sector
        sector_returns = {sector: np.mean(returns) for sector, returns in sector_data.items()}
        
        # Create treemap
        fig = go.Figure(go.Treemap(
            labels=list(sector_returns.keys()),
            parents=[""] * len(sector_returns),
            values=[abs(v) for v in sector_returns.values()],
            text=[f"{v:+.2f}%" for v in sector_returns.values()],
            textposition="middle center",
            marker=dict(
                colorscale='RdYlGn',
                cmid=0,
                colorbar=dict(title="Return %")
            )
        ))
        
        fig.update_layout(
            title="Sector Performance (1-Month Returns)",
            template='plotly_white',
            height=500
        )
        
        return fig
