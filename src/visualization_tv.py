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
        timeframe: str = "D",
        show_ema: bool = True,
        show_atr: bool = False,
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
        
        # Resample to Weekly if requested
        if timeframe == "W":
            # Set date as DatetimeIndex
            df[date_col] = pd.to_datetime(df[date_col])
            df.set_index(date_col, inplace=True)
            
            # Resample rule: W-FRI (weekly ending Friday)
            weekly_df = df.resample('W-FRI').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum',
                'EMA20': 'last',
                'EMA50': 'last',
                'EMA200': 'last'
            }).dropna(subset=['Open', 'High', 'Low', 'Close'])
            
            df = weekly_df.reset_index()
            date_col = df.columns[0]
            
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
                "wickDownColor": '#ef5350',
                "priceScaleId": "right"
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
                    
        # 2.5. ATR (Add on top of Candlesticks)
        if show_atr and analysis.atr and analysis.history is not None:
            # We calculate ATR 14 dynamically on the resampled timeframe for visual accuracy
            import numpy as np
            tr_df = df.copy()
            tr_df['PrevClose'] = tr_df['Close'].shift(1)
            tr_df['TR'] = np.maximum(
                tr_df['High'] - tr_df['Low'],
                np.maximum(
                    abs(tr_df['High'] - tr_df['PrevClose'].fillna(0)),
                    abs(tr_df['Low'] - tr_df['PrevClose'].fillna(0))
                )
            )
            tr_df['ATR14'] = tr_df['TR'].rolling(window=14).mean()
            
            atr_data = [{"time": row[date_col], "value": val} for _, row in tr_df.iterrows() if pd.notna(row['ATR14']) and (val := float(row['ATR14']))]
            if atr_data:
                series.append({
                    "type": 'Line',
                    "data": atr_data,
                    "options": {
                        "color": "#FFC107", 
                        "lineWidth": 2, 
                        "lineStyle": 2, 
                        "title": "ATR14",
                        "priceScaleId": 'atrScale',
                        "scaleMargins": {
                            "top": 0.8,
                            "bottom": 0,
                        }
                    }
                })

        # 3. Volume Histogram (on a separate scale)
        vol_data = [{"time": row[date_col], "value": row['Volume'], "color": 'rgba(38,166,154,0.3)' if row['Close'] >= row['Open'] else 'rgba(239,83,80,0.3)'} for _, row in df.iterrows()]
        
        series.append({
            "type": 'Histogram',
            "data": vol_data,
            "options": {
                "priceFormat": {"type": 'volume'},
                "priceScaleId": "volScale", 
                "scaleMargins": {
                    "top": 0.8,
                    "bottom": 0,
                },
            }
        })
        
        # 4. Markers (Earnings)
        markers = []
        
        # Helper to find closest trading day if earnings fall on weekend/holiday
        valid_dates_dt = pd.to_datetime(list(set(df[date_col].values)))
        
        def get_closest_trading_day(target_date):
            if valid_dates_dt.empty: return None
            # Find the closest date in the past or future
            target_dt = pd.to_datetime(target_date)
            closest_idx = (valid_dates_dt - target_dt).abs().argmin()
            return valid_dates_dt[closest_idx].strftime('%Y-%m-%d')
            
        if getattr(analysis, 'last_earnings_date', None):
            try:
                closest_date = get_closest_trading_day(analysis.last_earnings_date)
                if closest_date:
                    markers.append({
                        "time": closest_date,
                        "position": 'belowBar',
                        "color": '#2196F3',
                        "shape": 'arrowUp',
                        "text": 'E'
                    })
            except Exception:
                pass
                
        if getattr(analysis, 'next_earnings_date', None):
            try:
                closest_date = get_closest_trading_day(analysis.next_earnings_date)
                if closest_date:
                    markers.append({
                        "time": closest_date,
                        "position": 'belowBar',
                        "color": '#FF9800',
                        "shape": 'arrowUp',
                        "text": 'E (Est)'
                    })
            except Exception:
                pass

        # Render Lightweight Chart Component with Custom UI Overlay
        button_bg = "#262B33" if theme == 'dark' else "#F0F2F6"
        button_hover = "#3A414A" if theme == 'dark' else "#E0E4EB"
        button_text = "#FFFFFF" if theme == 'dark' else "#1E1E1E"
        
        st.components.v1.html(
            f'''
            <div style="position: relative; width: 100%; height: {height}px;">
                <div id="tvchart-toolbar" style="
                    position: absolute; 
                    top: 10px; 
                    left: 10px; 
                    z-index: 10; 
                    display: flex; 
                    gap: 5px;
                    background: {bg_color};
                    padding: 4px;
                    border-radius: 6px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                ">
                    <button class="tvc-btn" data-range="1W">1W</button>
                    <button class="tvc-btn" data-range="2W">2W</button>
                    <button class="tvc-btn" data-range="1M">1M</button>
                    <button class="tvc-btn" data-range="3M">3M</button>
                    <button class="tvc-btn" data-range="6M">6M</button>
                    <button class="tvc-btn" data-range="1Y">1Y</button>
                    <button class="tvc-btn" data-range="5Y">5Y</button>
                    <button class="tvc-btn" data-range="ALL">ALL</button>
                </div>
                <style>
                    .tvc-btn {{
                        background: {button_bg};
                        color: {button_text};
                        border: none;
                        padding: 4px 10px;
                        font-size: 12px;
                        font-family: inherit;
                        border-radius: 4px;
                        cursor: pointer;
                        transition: background 0.2s;
                    }}
                    .tvc-btn:hover {{ background: {button_hover}; }}
                    .tvc-btn.active {{ background: #2962FF; color: white; }}
                </style>
                <div id="tvchart-container" style="width: 100%; height: 100%; border-radius: 8px; overflow: hidden;"></div>
            </div>
            <script>
                // Include lightweight-charts script
                const script = document.createElement('script');
                script.src = "https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js";
                script.onload = () => {{
                    try {{
                        const chartOptions = {json.dumps(chartOptions)};
                        const chart = LightweightCharts.createChart(document.getElementById('tvchart-container'), chartOptions);
                        
                        // Price scales configuration
                        
                        // 1. Right scale (Main price content - restrict it to top 75% of chart)
                        chart.priceScale('right').applyOptions({{
                            'scaleMargins': {{
                                'top': 0.1,    // 10% from top
                                'bottom': 0.3, // Leave bottom 30% for volume/ATR
                            }},
                        }});
                        
                        // 2. volScale (Volume - restrict it to bottom 20%)
                        chart.priceScale('volScale').applyOptions({{
                            'scaleMargins': {{
                                'top': 0.8,    // Start 80% down
                                'bottom': 0,
                            }},
                        }});
                        
                        // 3. atrScale (ATR - overlaps Volume)
                        chart.priceScale('atrScale').applyOptions({{
                            'scaleMargins': {{
                                'top': 0.8, 
                                'bottom': 0,
                            }},
                            'visible': false, // Don't show confusing duplicate axis numbers
                        }});
                        
                        const seriesData = {json.dumps(series)};
                        
                        seriesData.forEach(s => {{
                            let seriesInstance;
                            if (s.type === 'Candlestick') {{
                                seriesInstance = chart.addCandlestickSeries(s.options);
                                seriesInstance.setData(s.data);
                                if (s.priceLines) {{
                                    s.priceLines.forEach(pl => seriesInstance.createPriceLine(pl));
                                }}
                                
                                const markers = {json.dumps(markers)};
                                if (markers.length > 0) {{
                                    seriesInstance.setMarkers(markers);
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
                        
                        // Setup Toolbar Buttons
                        const btns = document.querySelectorAll('.tvc-btn');
                        btns.forEach(btn => {{
                            btn.addEventListener('click', (e) => {{
                                btns.forEach(b => b.classList.remove('active'));
                                e.target.classList.add('active');
                                
                                const range = e.target.getAttribute('data-range');
                                const totalData = seriesData[0].data;
                                if(totalData.length === 0) return;
                                
                                const lastDateStr = totalData[totalData.length - 1].time;
                                const lastDate = new Date(lastDateStr);
                                let fromDate = new Date(lastDate);
                                
                                if(range === '1W') fromDate.setDate(lastDate.getDate() - 7);
                                else if(range === '2W') fromDate.setDate(lastDate.getDate() - 14);
                                else if(range === '1M') fromDate.setMonth(lastDate.getMonth() - 1);
                                else if(range === '3M') fromDate.setMonth(lastDate.getMonth() - 3);
                                else if(range === '6M') fromDate.setMonth(lastDate.getMonth() - 6);
                                else if(range === '1Y') fromDate.setFullYear(lastDate.getFullYear() - 1);
                                else if(range === '5Y') fromDate.setFullYear(lastDate.getFullYear() - 5);
                                else {{
                                    // ALL
                                    chart.timeScale().fitContent();
                                    return;
                                }}
                                
                                // Format fromDate to YYYY-MM-DD
                                const fromStr = fromDate.toISOString().split('T')[0];
                                chart.timeScale().setVisibleLogicalRange({{
                                    from: chart.timeScale().coordinateToLogical(chart.timeScale().width() - 100) || 0, // Fallback
                                    to: totalData.length - 1
                                }}); // Temporary reset
                                
                                // Find closest index
                                let closestIdx = 0;
                                for(let i = 0; i < totalData.length; i++){{
                                    if(new Date(totalData[i].time) >= fromDate) {{
                                        closestIdx = i;
                                        break;
                                    }}
                                }}
                                
                                chart.timeScale().setVisibleLogicalRange({{
                                    from: closestIdx,
                                    to: totalData.length + 5 // pad right
                                }});
                            }});
                        }});
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
