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

    def _build_series(self, df: pd.DataFrame, date_col: str, analysis: StockAnalysis, show_ema: bool, show_atr: bool, show_support_resistance: bool, show_trade_setup: bool) -> List[Dict[str, Any]]:
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
            
        candlestick_series = {
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
        }

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
                    "title": "E"
                })
            
            if getattr(analysis, 'suggested_stop_loss', None):
                price_lines.append({
                    "price": analysis.suggested_stop_loss,
                    "color": "#FF5252",
                    "lineWidth": 2,
                    "lineStyle": 2, # Dashed
                    "axisLabelVisible": True,
                    "title": "SL"
                })
                
            if getattr(analysis, 'max_buy_price', None):
                price_lines.append({
                    "price": analysis.max_buy_price,
                    "color": "#2196F3",
                    "lineWidth": 2,
                    "lineStyle": 1, # Dotted
                    "axisLabelVisible": True,
                    "title": "MBP"
                })

        if show_support_resistance:
            for i, level in enumerate(getattr(analysis, 'support_levels', [])):
                price_lines.append({
                    "price": level,
                    "color": "#808080",
                    "lineWidth": 1,
                    "lineStyle": 1, # Dotted
                    "axisLabelVisible": True,
                    "title": "S"
                })
            for i, level in enumerate(getattr(analysis, 'resistance_levels', [])):
                price_lines.append({
                    "price": level,
                    "color": "#E57373",
                    "lineWidth": 1,
                    "lineStyle": 1, # Dotted
                    "axisLabelVisible": True,
                    "title": "R"
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
            candlestick_series["priceLines"] = price_lines
            
        series.append(candlestick_series)

        # 2. EMAs
        for ema, color, width in [('EMA20', '#FF6D00', 1), ('EMA50', '#00E676', 1), ('EMA200', '#D500F9', 2)]:
            ema_data = []
            if show_ema and ema in df.columns:
                ema_data = [{"time": row[date_col], "value": val} for _, row in df.iterrows() if pd.notna(row[ema]) and (val := float(row[ema]))]
            series.append({
                "type": 'Line',
                "data": ema_data,
                "options": {"color": color, "lineWidth": width, "title": ema}
            })
                    
        # 3. ATR
        atr_data = []
        if show_atr and analysis.atr and analysis.history is not None:
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
             
        series.append({
            "type": 'Line',
            "data": atr_data,
            "options": {
                "color": "#FFC107", 
                "lineWidth": 2, 
                "lineStyle": 2, 
                "title": "ATR14",
                "priceScaleId": 'atrScale',
            }
        })

        # 4. Volume Histogram
        vol_data = [{"time": row[date_col], "value": row['Volume'], "color": 'rgba(38,166,154,0.3)' if row['Close'] >= row['Open'] else 'rgba(239,83,80,0.3)'} for _, row in df.iterrows()]
        
        vol_series = {
            "type": 'Histogram',
            "data": vol_data,
            "options": {
                "priceFormat": {"type": 'volume'},
                "priceScaleId": "volScale", 
            }
        }
        
        # Markers (Earnings) attach to Candlestick belowBar to avoid Volume pane clipping
        markers = []
        valid_dates = pd.to_datetime(df[date_col]).dt.strftime('%Y-%m-%d').tolist()
        max_date_str = max(valid_dates) if valid_dates else None
        
        def get_closest_past_trading_day(target_date):
            if not valid_dates: return None
            # Find exact or previous closest valid date in the data
            target_str = pd.to_datetime(target_date).strftime('%Y-%m-%d')
            if target_str in valid_dates:
                return target_str
            # If not exact, find the closest past date
            past_dates = [d for d in valid_dates if d <= target_str]
            return max(past_dates) if past_dates else None

        if getattr(analysis, 'past_earnings_dates', []):
            for past_date in analysis.past_earnings_dates:
                closest_date = get_closest_past_trading_day(past_date)
                if closest_date:
                    # check if already in markers to avoid duplicates
                    if not any(m['time'] == closest_date and m['text'] == 'E' for m in markers):
                        markers.append({
                            "time": closest_date,
                            "position": 'belowBar',
                            "color": '#2196F3',
                            "shape": 'arrowUp',
                            "text": 'E'
                        })
                
        if getattr(analysis, 'next_earnings_date', None):
            next_str = pd.to_datetime(analysis.next_earnings_date).strftime('%Y-%m-%d')
            # If it's in the future and not in the dataset yet, pad the datasets with whitespace!
            if max_date_str and next_str > max_date_str:
                series[0]["data"].append({"time": next_str})
                vol_data.append({"time": next_str})
                markers.append({
                    "time": next_str,
                    "position": 'belowBar',
                    "color": '#FF9800',
                    "shape": 'arrowUp',
                    "text": 'E'
                })
            else:
                closest_date = get_closest_past_trading_day(analysis.next_earnings_date)
                if closest_date:
                    markers.append({
                        "time": closest_date,
                        "position": 'belowBar',
                        "color": '#FF9800',
                        "shape": 'arrowUp',
                        "text": 'E'
                    })
            
        if markers:
            if "markers" not in series[0]:
                series[0]["markers"] = markers
            else:
                series[0]["markers"].extend(markers)
            
        series.append(vol_series)
        
        return series

    def generate_candlestick_chart(
        self,
        analysis: StockAnalysis,
        timeframe: str = "W",
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
            
        df.reset_index(inplace=True)
        date_col = 'Date' if 'Date' in df.columns else df.columns[0]
        df = df.dropna(subset=[date_col]).copy()
        
        # Determine Daily Series
        daily_df = df.copy()
        daily_df[date_col] = pd.to_datetime(daily_df[date_col]).dt.strftime('%Y-%m-%d')
        series_daily = self._build_series(daily_df, date_col, analysis, show_ema, show_atr, show_support_resistance, show_trade_setup)
        
        # Determine Weekly Series
        weekly_df = df.copy()
        weekly_df[date_col] = pd.to_datetime(weekly_df[date_col])
        weekly_df.set_index(date_col, inplace=True)
        
        agg_dict = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
        for col in ['EMA20', 'EMA50', 'EMA200']:
            if col in weekly_df.columns:
                agg_dict[col] = 'last'
                
        weekly_df = weekly_df.resample('W-FRI').agg(agg_dict).dropna(subset=['Open', 'High', 'Low', 'Close']).reset_index()
        weekly_df[date_col] = pd.to_datetime(weekly_df[date_col]).dt.strftime('%Y-%m-%d')
        series_weekly = self._build_series(weekly_df, date_col, analysis, show_ema, show_atr, show_support_resistance, show_trade_setup)

        theme = st.session_state.get('theme_preference', 'dark')
        bg_color = '#0E1117' if theme == 'dark' else '#FFFFFF'
        text_color = '#FFFFFF' if theme == 'dark' else '#1E1E1E'
        grid_color = '#1E2229' if theme == 'dark' else '#E0E0E0'

        chartOptions = {
            "layout": { "textColor": text_color, "background": {"type": "solid", "color": bg_color} },
            "grid": { "vertLines": {"color": grid_color, "style": 1}, "horzLines": {"color": grid_color, "style": 1} },
            "crosshair": { "mode": 1 },
            "priceScale": { "borderColor": grid_color },
            "timeScale": { "borderColor": grid_color, "timeVisible": True, "rightOffset": 15 }
        }

        button_bg = "#262B33" if theme == 'dark' else "#F0F2F6"
        button_hover = "#3A414A" if theme == 'dark' else "#E0E4EB"
        button_text = "#FFFFFF" if theme == 'dark' else "#1E1E1E"
        
        st.components.v1.html(
            f'''
            <div style="flex-direction: column; width: 100%; height: {height}px; display: flex; background: {bg_color}; border-radius: 8px; border: 1px solid {grid_color};">
                <div id="tvchart-toolbar" style="
                    display: flex; 
                    gap: 10px;
                    padding: 8px 15px;
                    border-bottom: 1px solid {grid_color};
                    align-items: center;
                    justify-content: space-between;
                ">
                    <div style="display: flex; gap: 5px; align-items: center;">
                        <span style="color: {text_color}; font-family: sans-serif; font-size: 13px; font-weight: bold; margin-right: 5px;">Views:</span>
                        <button class="tvc-tf-btn active" data-tf="D">Daily</button>
                        <button class="tvc-tf-btn" data-tf="W">Weekly</button>
                    </div>
                    <div style="display: flex; gap: 5px; align-items: center;">
                        <span style="color: {text_color}; font-family: sans-serif; font-size: 13px; font-weight: bold; margin-right: 5px;">Zoom:</span>
                        <button class="tvc-btn" data-range="1W">1W</button>
                        <button class="tvc-btn" data-range="2W">2W</button>
                        <button class="tvc-btn" data-range="1M">1M</button>
                        <button class="tvc-btn" data-range="3M">3M</button>
                        <button class="tvc-btn" data-range="6M">6M</button>
                        <button class="tvc-btn" data-range="1Y">1Y</button>
                        <button class="tvc-btn" data-range="5Y">5Y</button>
                        <button class="tvc-btn" data-range="ALL">ALL</button>
                    </div>
                </div>
                <style>
                    .tvc-btn, .tvc-tf-btn {{
                        background: {button_bg}; color: {button_text}; border: none;
                        padding: 4px 10px; font-size: 12px; font-family: inherit;
                        border-radius: 4px; cursor: pointer; transition: background 0.2s;
                    }}
                    .tvc-btn:hover, .tvc-tf-btn:hover {{ background: {button_hover}; }}
                    .tvc-btn.active, .tvc-tf-btn.active {{ background: #2962FF; color: white; }}
                </style>
                <div id="tvchart-container" style="flex: 1; width: 100%; overflow: hidden;"></div>
            </div>
            <script>
                const script = document.createElement('script');
                script.src = "https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js";
                script.onload = () => {{
                    try {{
                        const chartOptions = {json.dumps(chartOptions)};
                        const chart = LightweightCharts.createChart(document.getElementById('tvchart-container'), chartOptions);
                        
                        // Distinct Panes Setup using Scale Margins
                        const hasAtr = {str(show_atr).lower()};
                        
                        chart.priceScale('right').applyOptions({{
                            scaleMargins: {{ top: 0.05, bottom: hasAtr ? 0.35 : 0.25 }},
                        }});
                        
                        chart.priceScale('volScale').applyOptions({{
                            scaleMargins: {{ top: hasAtr ? 0.70 : 0.80, bottom: hasAtr ? 0.15 : 0 }},
                        }});
                        
                        chart.priceScale('atrScale').applyOptions({{
                            scaleMargins: {{ top: 0.88, bottom: 0 }},
                            visible: true, // Show ATR scale separately at the bottom
                            borderColor: '{grid_color}',
                        }});
                        
                        const datasets = {{
                            "D": {json.dumps(series_daily)},
                            "W": {json.dumps(series_weekly)}
                        }};
                        
                        let seriesInstances = [];
                        let currentTF = "{timeframe}";
                        if (!datasets[currentTF]) currentTF = "D";
                        
                        // Initialization routine
                        function initSeries() {{
                            datasets[currentTF].forEach((s, idx) => {{
                                let inst;
                                if (s.type === 'Candlestick') {{
                                    inst = chart.addCandlestickSeries(s.options);
                                    if (s.priceLines) s.priceLines.forEach(pl => inst.createPriceLine(pl));
                                }} else if (s.type === 'Line') {{
                                    inst = chart.addLineSeries(s.options);
                                }} else if (s.type === 'Histogram') {{
                                    inst = chart.addHistogramSeries(s.options);
                                }}
                                seriesInstances.push(inst);
                            }});
                        }}
                        
                        function applyData(tf) {{
                            datasets[tf].forEach((s, idx) => {{
                                seriesInstances[idx].setData(s.data);
                                if (s.type === 'Candlestick' || s.type === 'Histogram') {{
                                    if (s.markers) seriesInstances[idx].setMarkers(s.markers);
                                    else seriesInstances[idx].setMarkers([]); // clear explicit empty markers
                                }}
                            }});
                        }}
                        
                        initSeries();
                        applyData(currentTF);
                        
                        // Set active toggle visually based on python prop
                        document.querySelectorAll('.tvc-tf-btn').forEach(btn => {{
                            btn.classList.remove('active');
                            if(btn.getAttribute('data-tf') === currentTF) btn.classList.add('active');
                        }});
                        
                        // Default to 5Y zoom
                        setTimeout(() => {{
                            const defaultZoomBtn = document.querySelector('.tvc-btn[data-range="5Y"]');
                            if(defaultZoomBtn) defaultZoomBtn.click();
                        }}, 50);

                        // Resize observer
                        new ResizeObserver(entries => {{
                          if (entries.length === 0 || entries[0].target !== document.getElementById('tvchart-container')) return;
                          const newRect = entries[0].contentRect;
                          chart.applyOptions({{ width: newRect.width, height: newRect.height }});
                        }}).observe(document.getElementById('tvchart-container'));
                        
                        // Timeframe Toggles JS
                        document.querySelectorAll('.tvc-tf-btn').forEach(btn => {{
                            btn.addEventListener('click', (e) => {{
                                document.querySelectorAll('.tvc-tf-btn').forEach(b => b.classList.remove('active'));
                                e.target.classList.add('active');
                                const tf = e.target.getAttribute('data-tf');
                                applyData(tf);
                                currentTF = tf;
                                chart.timeScale().fitContent();
                            }});
                        }});
                        
                        // Range Toggles
                        const btns = document.querySelectorAll('.tvc-btn');
                        btns.forEach(btn => {{
                            btn.addEventListener('click', (e) => {{
                                btns.forEach(b => b.classList.remove('active'));
                                e.target.classList.add('active');
                                
                                const range = e.target.getAttribute('data-range');
                                const totalData = datasets[currentTF][0].data; // candlestick data
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
                                    chart.timeScale().fitContent();
                                    return;
                                }}
                                
                                let closestIdx = 0;
                                for(let i = 0; i < totalData.length; i++){{
                                    if(new Date(totalData[i].time) >= fromDate) {{
                                        closestIdx = i;
                                        break;
                                    }}
                                }}
                                
                                chart.timeScale().setVisibleLogicalRange({{
                                    from: chart.timeScale().coordinateToLogical(chart.timeScale().width() - 100) || 0,
                                    to: totalData.length - 1
                                }}); // Force refresh buffer
                                
                                setTimeout(() => {{
                                    chart.timeScale().setVisibleLogicalRange({{
                                        from: closestIdx,
                                        to: totalData.length + 5
                                    }});
                                }}, 10);
                            }});
                        }});
                    }} catch (e) {{
                        document.getElementById('tvchart-container').innerHTML = "<div style='color:#FF5252; padding: 20px; font-family: sans-serif;'><strong>Chart Error:</strong> " + e.message + "</div>";
                        console.error("TradingView Chart Error:", e);
                    }}
                }};
                script.onerror = () => {{
                    document.getElementById('tvchart-container').innerHTML = "<div style='color:#FF5252; padding: 20px; font-family: sans-serif;'><strong>Network Error:</strong> Failed to load charts.</div>";
                }};
                document.head.appendChild(script);
            </script>
            ''',
            height=height
        )
