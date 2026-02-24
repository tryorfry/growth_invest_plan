"""
Plotly-based chart generator for interactive visualizations
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st
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
        show_trade_setup: bool = False,
        show_rsi: bool = False,
        show_macd: bool = False
    ) -> Optional[go.Figure]:
        """
        Generate an interactive candlestick chart with technical indicators and subplots.
        
        Args:
            analysis: StockAnalysis object containing historical data
            show_ema: Whether to show EMA lines
            show_bollinger: Whether to show Bollinger Bands
            show_support_resistance: Whether to show Support/Resistance levels
            show_trade_setup: Whether to show Trade Setup (Entry/Stop)
            show_rsi: Whether to include RSI subplot
            show_macd: Whether to include MACD subplot
            
        Returns:
            Plotly Figure object or None if no data
        """
        if analysis.history is None or analysis.history.empty:
            return None
        
        df = analysis.history.copy()
        
        # Determine number of rows and heights
        rows = 2
        titles = [f'{analysis.ticker} Price Chart', 'Volume']
        row_heights = [0.5, 0.15] # Default for Price + Volume
        
        rsi_row = 0
        if show_rsi and 'RSI' in df.columns:
            rows += 1
            rsi_row = rows
            titles.append('RSI')
            row_heights.append(0.175)
            
        macd_row = 0
        if show_macd and 'MACD' in df.columns:
            rows += 1
            macd_row = rows
            titles.append('MACD')
            row_heights.append(0.175)

        # Normalize row heights to sum to 1
        total_height = sum(row_heights)
        normalized_heights = [h/total_height for h in row_heights]
        
        # Create figure with shared x-axes
        fig = make_subplots(
            rows=rows, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=normalized_heights,
            subplot_titles=titles
        )
        
        # 1. Candlestick (Row 1)
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
        
        # EMAs (Row 1)
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
        
        # Bollinger Bands (Row 1)
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
        
        # Price Target Line (Row 1)
        if analysis.median_price_target:
            fig.add_trace(
                go.Scatter(
                    x=[df.index[0], df.index[-1]],
                    y=[analysis.median_price_target, analysis.median_price_target],
                    mode="lines",
                    name=f"Target: ${analysis.median_price_target:.2f}",
                    line=dict(color="green", width=2, dash="dash"),
                    hoverinfo="skip"
                ),
                row=1, col=1
            )
            
        # Support and Resistance (Row 1)
        if show_support_resistance:
            # High Volume Nodes
            for i, hvn in enumerate(getattr(analysis, 'volume_profile_hvns', [])):
                fig.add_trace(
                    go.Scatter(
                        x=[df.index[0], df.index[-1]],
                        y=[hvn, hvn],
                        mode="lines",
                        name=f"HVN {i+1}: ${hvn:.2f}",
                        line=dict(color="rgba(128, 0, 128, 0.4)", width=3),
                        hoverinfo="name+y"
                    ),
                    row=1, col=1
                )
            
            # Support levels
            for i, level in enumerate(getattr(analysis, 'support_levels', [])):
                name = f"Support {i+1}: ${level:.2f}"
                fig.add_trace(
                    go.Scatter(
                        x=[df.index[0], df.index[-1]],
                        y=[level, level],
                        mode="lines",
                        name=name,
                        line=dict(color="green", width=1, dash="dot"),
                        opacity=0.8,
                        hoverinfo="name+y"
                    ),
                    row=1, col=1
                )
            
            # Resistance levels
            for i, level in enumerate(getattr(analysis, 'resistance_levels', [])):
                name = f"Resistance {i+1}: ${level:.2f}"
                fig.add_trace(
                    go.Scatter(
                        x=[df.index[0], df.index[-1]],
                        y=[level, level],
                        mode="lines",
                        name=name,
                        line=dict(color="red", width=1, dash="dot"),
                        opacity=0.8,
                        hoverinfo="name+y"
                    ),
                    row=1, col=1
                )
        
        # Trade Setup (Entry & Stop Loss) (Row 1)
        if show_trade_setup:
            if getattr(analysis, 'suggested_entry', None):
                fig.add_trace(
                    go.Scatter(
                        x=[df.index[0], df.index[-1]],
                        y=[analysis.suggested_entry, analysis.suggested_entry],
                        mode="lines",
                        name=f"ENTRY: ${analysis.suggested_entry:.2f}",
                        line=dict(color="#0000FF", width=2), # Bright Blue
                        hoverinfo="name+y"
                    ),
                    row=1, col=1
                )
                
            if getattr(analysis, 'suggested_stop_loss', None):
                fig.add_trace(
                    go.Scatter(
                        x=[df.index[0], df.index[-1]],
                        y=[analysis.suggested_stop_loss, analysis.suggested_stop_loss],
                        mode="lines",
                        name=f"STOP: ${analysis.suggested_stop_loss:.2f}",
                        line=dict(color="#FF0000", width=2), # Bright Red
                        hoverinfo="name+y"
                    ),
                    row=1, col=1
                )

        # 2. Volume bars (Row 2)
        colors = ['red' if row['Close'] < row['Open'] else 'green' for _, row in df.iterrows()]
        fig.add_trace(
            go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color=colors, showlegend=False),
            row=2, col=1
        )
        
        # 3. RSI (Optional Row)
        if rsi_row:
            fig.add_trace(
                go.Scatter(
                    x=df.index, y=df['RSI'], name='RSI',
                    line=dict(color='purple', width=2)
                ),
                row=rsi_row, col=1
            )
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=rsi_row, col=1, annotation_text="70")
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=rsi_row, col=1, annotation_text="30")
        
        # 4. MACD (Optional Row)
        if macd_row:
            fig.add_trace(
                go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue', width=2)),
                row=macd_row, col=1
            )
            if 'MACD_Signal' in df.columns:
                fig.add_trace(
                    go.Scatter(x=df.index, y=df['MACD_Signal'], name='MACD Signal', line=dict(color='orange', width=2)),
                    row=macd_row, col=1
                )
                histogram = df['MACD'] - df['MACD_Signal']
                hist_colors = ['green' if val >= 0 else 'red' for val in histogram]
                fig.add_trace(
                    go.Bar(x=df.index, y=histogram, name='MACD Histogram', marker_color=hist_colors, opacity=0.3),
                    row=macd_row, col=1
                )
            fig.add_hline(y=0, line_dash="dash", line_color="gray", row=macd_row, col=1)

        # Determine theme
        theme = st.session_state.get('theme_preference', 'dark')
        template = 'plotly_white' if theme == 'light' else 'plotly_dark'
        grid_color = 'rgba(128, 128, 128, 0.1)'

        # Overall Layout
        total_fig_height = 850 + (200 if rsi_row else 0) + (200 if macd_row else 0)
        
        fig.update_layout(
            title=dict(
                text=f'<b>{analysis.ticker}</b> Interactive Analysis',
                x=0.05,
                font=dict(size=24)
            ),
            height=total_fig_height,
            hovermode='x unified',
            template=template,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                bgcolor='rgba(0,0,0,0)'
            ),
            margin=dict(t=120, b=50, l=50, r=50), # Decouple buttons and price chart
            hoverlabel=dict(
                bgcolor="rgba(0,0,0,0.8)" if theme == 'dark' else "rgba(255,255,255,0.8)",
                font_size=12,
                font_family="Inter, sans-serif"
            )
        )
        
        # Configure X-Axes (Shared)
        fig.update_xaxes(
            showspikes=True,
            spikemode='across',
            spikesnap='cursor',
            spikethickness=1,
            spikedash='dash',
            spikecolor='#999999',
            rangeselector=dict(
                buttons=list([
                    dict(count=7, label="1W", step="day", stepmode="backward"),
                    dict(count=14, label="2W", step="day", stepmode="backward"),
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(count=5, label="5Y", step="year", stepmode="backward"),
                    dict(step="all", label="All")
                ]),
                bgcolor="rgba(150, 150, 150, 0.1)",
                activecolor="rgba(25, 118, 210, 0.5)",
                font=dict(size=12, weight='bold'),
                y=1.08 # Move buttons higher to avoid clutter
            ),
            gridcolor=grid_color,
            row=1, col=1
        )
        
        # Rangeslider on the bottom row
        fig.update_xaxes(rangeslider_visible=True, row=rows, col=1)
        
        # Configure Y-Axes with Spikelines
        fig.update_yaxes(
            showspikes=True,
            spikemode='across',
            spikethickness=1,
            spikedash='dash',
            spikecolor='#999999',
            gridcolor=grid_color
        )

        # Price Annotation (Current Price)
        fig.add_annotation(
            xref="paper", yref="y1",
            x=1, y=analysis.current_price,
            text=f" <b>${analysis.current_price:.2f}</b> ",
            showarrow=False,
            font=dict(size=12, color="white"),
            bgcolor="#2576d2",
            bordercolor="#2576d2",
            borderwidth=2,
            borderpad=4,
            align="left",
            xanchor="left"
        )
        
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        if rsi_row:
            fig.update_yaxes(title_text="RSI", range=[0, 100], row=rsi_row, col=1)
        if macd_row:
            fig.update_yaxes(title_text="MACD", row=macd_row, col=1)
        
        # Adjust vertical spacing for subplots
        fig.update_layout(vertical_spacing=0.06)
        
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
        
        # Determine template
        theme = st.session_state.get('theme_preference', 'dark')
        template = 'plotly_white' if theme == 'light' else 'plotly_dark'

        fig.update_layout(
            title='Relative Strength Index (RSI)',
            yaxis_title='RSI',
            xaxis_title='Date',
            height=300,
            template=template,
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
        
        # Determine template
        theme = st.session_state.get('theme_preference', 'dark')
        template = 'plotly_white' if theme == 'light' else 'plotly_dark'

        fig.update_layout(
            title='MACD (Moving Average Convergence Divergence)',
            yaxis_title='MACD',
            xaxis_title='Date',
            height=300,
            template=template
        )
        
        return fig
