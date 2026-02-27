"""
TradingView Lightweight Charts generator for highly interactive visualizations
"""
import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List
from streamlit_lightweight_charts import renderLightweightCharts
import json

from .analyzer import StockAnalysis

class TVChartGenerator:
    """Generates ultra-interactive TradingView Lightweight Charts"""

    def generate_candlestick_chart(
        self,
        analysis: StockAnalysis,
        show_ema: bool = True,
        show_support_resistance: bool = True,
        show_trade_setup: bool = True,
        height: int = 600
    ) -> None:
        """
        Renders an interactive TradingView lightweight chart directly into Streamlit.
        """
        if analysis.history is None or analysis.history.empty:
            st.warning("No historical data available for chart.")
            return

        df = analysis.history.copy()
        
        # Clean dataframe to prevent JSON formatting errors with NaNs or NaTs that crash JS charts
        missing_cols = [c for c in ['Open', 'High', 'Low', 'Close'] if c not in df.columns]
        if missing_cols:
            st.warning(f"Missing required price columns for chart: {missing_cols}")
            return
            
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close']).copy()
        if 'Volume' in df.columns:
            df['Volume'] = df['Volume'].fillna(0)
            
        if df.empty:
            st.warning("No complete historical data available for chart.")
            return
            
        # Reset index to get Date as a column, format to string YYYY-MM-DD
        df.reset_index(inplace=True)
        # Rename date column if it was named correctly or implicitly 'Date'
        date_col = 'Date' if 'Date' in df.columns else df.columns[0]
        # Ensure we don't have NaT dates
        df = df.dropna(subset=[date_col]).copy()
        df[date_col] = pd.to_datetime(df[date_col]).dt.strftime('%Y-%m-%d')

        theme = st.session_state.get('theme_preference', 'dark')
        bg_color = '#0E1117' if theme == 'dark' else '#FFFFFF'
        text_color = '#FFFFFF' if theme == 'dark' else '#1E1E1E'
        grid_color = '#1E2229' if theme == 'dark' else '#E0E0E0'

        # Overall Chart Options
        chartOptions = {
            "layout": {
                "textColor": text_color,
                "background": {"type": "solid", "color": bg_color},
            },
            "grid": {
                "vertLines": {"color": grid_color, "style": 1},
                "horzLines": {"color": grid_color, "style": 1},
            },
            "crosshair": {
                "mode": 1, # 0 for "Normal", 1 for "Magnet"
            },
            "priceScale": {
                "borderColor": grid_color,
            },
            "timeScale": {
                "borderColor": grid_color,
                "timeVisible": True,
                "rightOffset": 15,
            }
        }

        series = []

        # 1. Candlestick Series
        candles_data = []
        for _, row in df.iterrows():
            candles_data.append({
                "time": row[date_col],
                "open": row['Open'],
                "high": row['High'],
                "low": row['Low'],
                "close": row['Close'],
            })
            
        series.append({
            "type": 'Candlestick',
            "data": candles_data,
            "options": {
                "upColor": '#26a69a',
                "downColor": '#ef5350',
                "borderVisible": False,
                "wickUpColor": '#26a69a',
                "wickDownColor": '#ef5350'
            }
        })

        # Base series price scale configuration
        # Price lines (Horizontal markers) for candlestick overlay
        price_lines = []

        if show_trade_setup:
            if getattr(analysis, 'suggested_entry', None):
                price_lines.append({
                    "price": analysis.suggested_entry,
                    "color": "#00E676",
                    "lineWidth": 2,
                    "lineStyle": 0, # Solid
                    "axisLabelVisible": True,
                    "title": "ENTRY"
                })
            
            if getattr(analysis, 'suggested_stop_loss', None):
                price_lines.append({
                    "price": analysis.suggested_stop_loss,
                    "color": "#FF5252",
                    "lineWidth": 2,
                    "lineStyle": 2, # Dashed
                    "axisLabelVisible": True,
                    "title": "STOP"
                })

        if show_support_resistance:
            for i, level in enumerate(getattr(analysis, 'support_levels', [])):
                price_lines.append({
                    "price": level,
                    "color": "#808080",
                    "lineWidth": 1,
                    "lineStyle": 1, # Dotted
                    "axisLabelVisible": True,
                    "title": "SUPP"
                })
            for i, level in enumerate(getattr(analysis, 'resistance_levels', [])):
                price_lines.append({
                    "price": level,
                    "color": "#E57373",
                    "lineWidth": 1,
                    "lineStyle": 1, # Dotted
                    "axisLabelVisible": True,
                    "title": "RES"
                })
                
            for hvn in getattr(analysis, 'volume_profile_hvns', []):
                 price_lines.append({
                    "price": hvn,
                    "color": "rgba(91, 33, 182, 0.7)", # Purple
                    "lineWidth": 3,
                    "lineStyle": 0,
                    "axisLabelVisible": False,
                    "title": "HVN"
                })

        if price_lines:
            series[0]["priceLines"] = price_lines

        # 2. EMAs (Add on top of Candlesticks)
        if show_ema:
            if 'EMA20' in df.columns:
                ema_data = [{"time": row[date_col], "value": val} for _, row in df.iterrows() if pd.notna(row['EMA20']) and (val := float(row['EMA20']))]
                if ema_data:
                    series.append({
                        "type": 'Line',
                        "data": ema_data,
                        "options": {"color": "#FF6D00", "lineWidth": 1, "title": "EMA20"}
                    })
            if 'EMA50' in df.columns:
                ema_data = [{"time": row[date_col], "value": val} for _, row in df.iterrows() if pd.notna(row['EMA50']) and (val := float(row['EMA50']))]
                if ema_data:
                    series.append({
                        "type": 'Line',
                        "data": ema_data,
                        "options": {"color": "#00E676", "lineWidth": 1, "title": "EMA50"}
                    })
            if 'EMA200' in df.columns:
                ema_data = [{"time": row[date_col], "value": val} for _, row in df.iterrows() if pd.notna(row['EMA200']) and (val := float(row['EMA200']))]
                if ema_data:
                    series.append({
                        "type": 'Line',
                        "data": ema_data,
                        "options": {"color": "#D500F9", "lineWidth": 2, "title": "EMA200"}
                    })

        # 3. Volume Histogram (on a separate scale)
        vol_data = []
        for _, row in df.iterrows():
            vol_data.append({
                "time": row[date_col],
                "value": row['Volume'],
                "color": 'rgba(0, 150, 136, 0.5)' if row['Close'] >= row['Open'] else 'rgba(255, 82, 82, 0.5)'
            })

        series.append({
            "type": 'Histogram',
            "data": vol_data,
            "options": {
                "color": '#26a69a',
                "priceFormat": {"type": 'volume'},
                "priceScaleId": "", # Set as an overlay
                "scaleMargins": {
                    "top": 0.8,
                    "bottom": 0,
                },
            }
        })

        # Render Lightweight Chart Component
        st.components.v1.html(
            f'''
            <div id="tvchart-container" style="width: 100%; height: {height}px; border-radius: 8px; overflow: hidden;"></div>
            <script>
                // Include lightweight-charts script
                const script = document.createElement('script');
                script.src = "https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js";
                script.onload = () => {{
                    try {{
                        const chartOptions = {json.dumps(chartOptions)};
                        const chart = LightweightCharts.createChart(document.getElementById('tvchart-container'), chartOptions);
                        
                        const seriesData = {json.dumps(series)};
                        
                        seriesData.forEach(s => {{
                            let seriesInstance;
                            if (s.type === 'Candlestick') {{
                                seriesInstance = chart.addCandlestickSeries(s.options);
                                seriesInstance.setData(s.data);
                                if (s.priceLines) {{
                                    s.priceLines.forEach(pl => seriesInstance.createPriceLine(pl));
                                }}
                            }} else if (s.type === 'Line') {{
                                seriesInstance = chart.addLineSeries(s.options);
                                seriesInstance.setData(s.data);
                            }} else if (s.type === 'Histogram') {{
                                seriesInstance = chart.addHistogramSeries(s.options);
                                seriesInstance.setData(s.data);
                            }}
                        }});
                        
                        // Force resize observer to adapt smoothly
                        new ResizeObserver(entries => {{
                          if (entries.length === 0 || entries[0].target !== document.getElementById('tvchart-container')) {{ return; }}
                          const newRect = entries[0].contentRect;
                          chart.applyOptions({{ width: newRect.width, height: newRect.height }});
                        }}).observe(document.getElementById('tvchart-container'));
                    }} catch (e) {{
                        document.getElementById('tvchart-container').innerHTML = "<div style='color:#FF5252; padding: 20px; font-family: sans-serif;'><strong>Chart Error:</strong> " + e.message + "</div>";
                        console.error("TradingView Chart Error:", e);
                    }}
                }};
                script.onerror = () => {{
                    document.getElementById('tvchart-container').innerHTML = "<div style='color:#FF5252; padding: 20px; font-family: sans-serif;'><strong>Network Error:</strong> Failed to fetch TradingView lightweight-charts. Check your internet connection or ad blocker.</div>";
                }};
                document.head.appendChild(script);
            </script>
            ''',
            height=height
        )
