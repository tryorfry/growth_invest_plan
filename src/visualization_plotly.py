"""
Plotly-based chart generator for interactive visualizations
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Optional
from .analyzer import StockAnalysis


class PlotlyChartGenerator:
    """Generates interactive Plotly charts for stock analysis"""
    
    def generate_candlestick_chart(
        self, 
        analysis: StockAnalysis,
        show_ema: bool = True,
        show_bollinger: bool = False,
        show_support_resistance: bool = False,
        show_trade_setup: bool = False
    ) -> Optional[go.Figure]:
        """
        Generate an interactive candlestick chart with technical indicators.
        
        Args:
            analysis: StockAnalysis object containing historical data
            show_ema: Whether to show EMA lines
            show_bollinger: Whether to show Bollinger Bands
            show_support_resistance: Whether to show Support/Resistance levels
            show_trade_setup: Whether to show Trade Setup (Entry/Stop)
            
        Returns:
            Plotly Figure object or None if no data
        """
        if analysis.history is None or analysis.history.empty:
            return None
        
        df = analysis.history.copy()
        
        # Create figure with secondary y-axis for volume
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{analysis.ticker} Price Chart', 'Volume')
        )
        
        # Candlestick
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Price',
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350'
            ),
            row=1, col=1
        )
        
        # EMAs
        if show_ema:
            if 'EMA20' in df.columns:
                fig.add_trace(
                    go.Scatter(x=df.index, y=df['EMA20'], name='EMA20', 
                              line=dict(color='blue', width=1)),
                    row=1, col=1
                )
            if 'EMA50' in df.columns:
                fig.add_trace(
                    go.Scatter(x=df.index, y=df['EMA50'], name='EMA50',
                              line=dict(color='orange', width=1)),
                    row=1, col=1
                )
            if 'EMA200' in df.columns:
                fig.add_trace(
                    go.Scatter(x=df.index, y=df['EMA200'], name='EMA200',
                              line=dict(color='red', width=1.5)),
                    row=1, col=1
                )
        
        # Bollinger Bands
        if show_bollinger and 'Bollinger_Upper' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df['Bollinger_Upper'], name='BB Upper',
                    line=dict(color='gray', width=1, dash='dash'),
                    showlegend=True
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df['Bollinger_Lower'], name='BB Lower',
                    line=dict(color='gray', width=1, dash='dash'),
                    fill='tonexty', fillcolor='rgba(128,128,128,0.1)',
                    showlegend=True
                ),
                row=1, col=1
            )
        
        # Price Target Line
        if analysis.median_price_target:
            fig.add_hline(
                y=analysis.median_price_target,
                line_dash="dash",
                line_color="green",
                annotation_text=f"Target: ${analysis.median_price_target:.2f}",
                row=1, col=1
            )
            
        # Support and Resistance
        if show_support_resistance:
            # Support levels
            for level in getattr(analysis, 'support_levels', []):
                fig.add_hline(
                    y=level,
                    line_dash="dot",
                    line_color="green",
                    line_width=1,
                    opacity=0.7,
                    annotation_text=f"Support: ${level:.2f}",
                    annotation_position="bottom right",
                    row=1, col=1
                )
            
            # Resistance levels
            for level in getattr(analysis, 'resistance_levels', []):
                fig.add_hline(
                    y=level,
                    line_dash="dot",
                    line_color="red",
                    line_width=1,
                    opacity=0.7,
                    annotation_text=f"Resistance: ${level:.2f}",
                    annotation_position="top right",
                    row=1, col=1
                )
        
        # Trade Setup (Entry & Stop Loss)
        if show_trade_setup:
            if getattr(analysis, 'suggested_entry', None):
                fig.add_hline(
                    y=analysis.suggested_entry,
                    line_dash="solid",
                    line_color="blue",
                    line_width=2,
                    annotation_text=f"ENTRY: ${analysis.suggested_entry:.2f}",
                    annotation_position="right",
                    row=1, col=1
                )
                
            if getattr(analysis, 'suggested_stop_loss', None):
                fig.add_hline(
                    y=analysis.suggested_stop_loss,
                    line_dash="solid",
                    line_color="red",
                    line_width=2,
                    annotation_text=f"STOP: ${analysis.suggested_stop_loss:.2f} (ATR)",
                    annotation_position="right",
                    row=1, col=1
                )

        # Volume bars
        colors = ['red' if row['Close'] < row['Open'] else 'green' for _, row in df.iterrows()]
        fig.add_trace(
            go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color=colors, showlegend=False),
            row=2, col=1
        )
        
        # Update layout
        fig.update_layout(
            title=f'{analysis.ticker} Technical Analysis',
            yaxis_title='Price ($)',
            xaxis_rangeslider_visible=False,
            height=700,
            hovermode='x unified',
            template='plotly_white'
        )
        
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        
        return fig
    
    def generate_rsi_chart(self, analysis: StockAnalysis) -> Optional[go.Figure]:
        """
        Generate RSI indicator chart.
        
        Args:
            analysis: StockAnalysis object
            
        Returns:
            Plotly Figure object or None
        """
        if analysis.history is None or 'RSI' not in analysis.history.columns:
            return None
        
        df = analysis.history.copy()
        
        fig = go.Figure()
        
        # RSI line
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['RSI'], name='RSI',
                line=dict(color='purple', width=2)
            )
        )
        
        # Overbought/Oversold lines
        fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
        fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")
        
        fig.update_layout(
            title='Relative Strength Index (RSI)',
            yaxis_title='RSI',
            xaxis_title='Date',
            height=300,
            template='plotly_white',
            yaxis=dict(range=[0, 100])
        )
        
        return fig
    
    def generate_macd_chart(self, analysis: StockAnalysis) -> Optional[go.Figure]:
        """
        Generate MACD indicator chart.
        
        Args:
            analysis: StockAnalysis object
            
        Returns:
            Plotly Figure object or None
        """
        if analysis.history is None or 'MACD' not in analysis.history.columns:
            return None
        
        df = analysis.history.copy()
        
        fig = go.Figure()
        
        # MACD line
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['MACD'], name='MACD',
                line=dict(color='blue', width=2)
            )
        )
        
        # Signal line
        if 'MACD_Signal' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df['MACD_Signal'], name='Signal',
                    line=dict(color='orange', width=2)
                )
            )
            
            # Histogram (MACD - Signal)
            histogram = df['MACD'] - df['MACD_Signal']
            colors = ['green' if val >= 0 else 'red' for val in histogram]
            fig.add_trace(
                go.Bar(
                    x=df.index, y=histogram, name='Histogram',
                    marker_color=colors, opacity=0.3
                )
            )
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        
        fig.update_layout(
            title='MACD (Moving Average Convergence Divergence)',
            yaxis_title='MACD',
            xaxis_title='Date',
            height=300,
            template='plotly_white'
        )
        
        return fig
