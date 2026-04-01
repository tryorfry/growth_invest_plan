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

    def _build_series(self, df: pd.DataFrame, date_col: str, analysis: StockAnalysis, show_ema: bool, show_atr: bool, show_rsi: bool, show_macd: bool, show_bollinger: bool, show_support_resistance: bool, show_hvn: bool, show_trade_setup: bool, show_channel: bool = True, user_annotations: list = None) -> List[Dict[str, Any]]:
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
                    "color": "#00C853", # Darker Green
                    "lineWidth": 2,
                    "lineStyle": 0, # Solid
                    "axisLabelVisible": True,
                    "title": "E"
                })
            
            if getattr(analysis, 'suggested_stop_loss', None):
                price_lines.append({
                    "price": analysis.suggested_stop_loss,
                    "color": "#D50000", # Darker Red
                    "lineWidth": 2,
                    "lineStyle": 2, # Dashed
                    "axisLabelVisible": True,
                    "title": "SL"
                })
                
            matp = getattr(analysis, 'median_price_target', None)
            mbp = getattr(analysis, 'max_buy_price', None)
            target = getattr(analysis, 'target_price', None)
            
            # 1. Handle MBP and MATP overlap
            if matp and mbp and abs(matp - mbp) < 0.01:
                price_lines.append({
                    "price": mbp,
                    "color": "#FFEB3B", # Yellow for combined
                    "lineWidth": 2,
                    "lineStyle": 0, # Solid
                    "axisLabelVisible": True,
                    "title": "MATP/MBP"
                })
            else:
                # Show separately
                if mbp:
                    price_lines.append({
                        "price": mbp,
                        "color": "#2196F3",
                        "lineWidth": 1.5,
                        "lineStyle": 0, # Solid
                        "axisLabelVisible": True,
                        "title": "MBP"
                    })
            if matp:
                title = "MATP"
                # If it exactly matches the PT/T target, combine labels
                if target and abs(matp - target) < 0.01:
                    title = f"MATP/{'PT' if analysis.trading_style == 'Swing Trading' else 'T'}"
                
                price_lines.append({
                    "price": matp,
                    "color": "#FFEB3B", # Yellow for MATP
                    "lineWidth": 1.5,
                    "lineStyle": 2, # Dashed
                    "axisLabelVisible": True,
                    "title": title
                })
            
            # 2. Show Profit Target (only if not already shown as part of MATP)
            if target and (not matp or abs(matp - target) >= 0.01):
                title = "PT" if analysis.trading_style == 'Swing Trading' else "T"
                price_lines.append({
                    "price": target,
                    "color": "#00E5FF", # Cyan for profit target
                    "lineWidth": 2,
                    "lineStyle": 1, # Dotted
                    "axisLabelVisible": True,
                    "title": title
                })

        if show_support_resistance:
            theme = st.session_state.get('theme_preference', 'dark')
            support_color = "#FFFFFF" if theme == 'dark' else "#000000"
            for i, level in enumerate(getattr(analysis, 'support_levels', [])):
                price_lines.append({
                    "price": level,
                    "color": support_color, # White in Dark Mode, Black in Light Mode
                    "lineWidth": 2, # Thicker for visibility
                    "lineStyle": 0, # Solid
                    "axisLabelVisible": True,
                    "title": "S"
                })
            for i, level in enumerate(getattr(analysis, 'resistance_levels', [])):
                price_lines.append({
                    "price": level,
                    "color": "#B71C1C", # Dark Red
                    "lineWidth": 2, # Thicker for visibility
                    "lineStyle": 0, # Solid
                    "axisLabelVisible": True,
                    "title": "R"
                })
                
        if show_hvn:
            for hvn in getattr(analysis, 'volume_profile_hvns', []):
                 price_lines.append({
                    "price": hvn,
                    "color": "rgba(91, 33, 182, 0.7)", # Purple
                    "lineWidth": 1.5,
                    "lineStyle": 0,
                    "axisLabelVisible": True,
                    "title": "HVN"
                })
                
        # Inject Custom User Annotations
        if user_annotations:
            for ann in user_annotations:
                line_color = "#FF00FF" # Magenta default
                if ann.annotation_type == 'support':
                    line_color = "#2E7D32" # Green
                elif ann.annotation_type == 'resistance':
                    line_color = "#B71C1C" # Red
                
                title = f"{ann.annotation_type.upper()[:3]}"
                if ann.text_note:
                    title += f": {ann.text_note}"
                    
                price_lines.append({
                    "price": ann.price_level,
                    "color": line_color,
                    "lineWidth": 2,
                    "lineStyle": 1, # Dotted
                    "axisLabelVisible": True,
                    "title": title[:30] # Truncate long notes
                })

        candlestick_series["priceLines"] = price_lines
        series.append(candlestick_series)

        # 2. EMAs
        for ema, color, width in [('EMA20', '#FF5252', 1.5), ('EMA50', '#00E676', 1.5), ('EMA200', '#D500F9', 1.5)]:
            ema_data = []
            if show_ema and ema in df.columns:
                ema_data = [{"time": row[date_col], "value": val} for _, row in df.iterrows() if pd.notna(row[ema]) and (val := float(row[ema]))]
            series.append({
                "type": 'Line',
                "data": ema_data,
                "options": {"color": color, "lineWidth": width, "title": ema, "priceScaleId": "right"}
            })
                    
        # 2.5 BOLL
        if show_bollinger and 'Bollinger_Upper' in df.columns and 'Bollinger_Lower' in df.columns:
            series.append({
                "type": 'Line',
                "data": [{"time": row[date_col], "value": float(row['Bollinger_Upper'])} for _, row in df.iterrows() if pd.notna(row['Bollinger_Upper'])],
                "options": {"color": 'rgba(33, 150, 243, 0.4)', "lineWidth": 1.5, "lineStyle": 2, "title": "Upper BOLL", "priceScaleId": "right"}
            })
            series.append({
                "type": 'Line',
                "data": [{"time": row[date_col], "value": float(row['Bollinger_Lower'])} for _, row in df.iterrows() if pd.notna(row['Bollinger_Lower'])],
                "options": {"color": 'rgba(33, 150, 243, 0.4)', "lineWidth": 1.5, "lineStyle": 2, "title": "Lower BOLL", "priceScaleId": "right"}
            })

        # 2.7 Trend Channel (parallel High/Low regression bands)
        if show_channel and getattr(analysis, 'trading_style', '') == 'Trend Trading' and 'Trend_Center' in df.columns:
            series.append({
                "type": 'Line',
                "data": [{"time": row[date_col], "value": float(row['Trend_Center'])} for _, row in df.iterrows() if pd.notna(row['Trend_Center'])],
                "options": {"color": '#FF9800', "lineWidth": 2, "lineStyle": 0, "title": "Channel Mid", "priceScaleId": "right", "lastValueVisible": True, "priceLineVisible": False}
            })
            series.append({
                "type": 'Line',
                "data": [{"time": row[date_col], "value": float(row['Trend_Upper'])} for _, row in df.iterrows() if pd.notna(row['Trend_Upper'])],
                "options": {"color": '#FF5722', "lineWidth": 1.5, "lineStyle": 2, "title": "Channel Top", "priceScaleId": "right", "lastValueVisible": True, "priceLineVisible": False}
            })
            series.append({
                "type": 'Line',
                "data": [{"time": row[date_col], "value": float(row['Trend_Lower'])} for _, row in df.iterrows() if pd.notna(row['Trend_Lower'])],
                "options": {"color": '#4CAF50', "lineWidth": 1.5, "lineStyle": 2, "title": "Channel Bot", "priceScaleId": "right", "lastValueVisible": True, "priceLineVisible": False}
            })

        # 3. ATR
        atr_data = []
        is_daily_style = getattr(analysis, 'trading_style', '') in ['Swing Trading', 'Trend Trading']
        atr_col = 'ATR_Daily' if is_daily_style else 'ATR'
        atr_label = 'ATR (14d)' if is_daily_style else 'ATR (14w)'
        
        if show_atr and atr_col in df.columns:
             atr_data = [{"time": row[date_col], "value": val} for _, row in df.iterrows() if pd.notna(row[atr_col]) and (val := float(row[atr_col]))]
             
        series.append({
            "type": 'Line',
            "data": atr_data,
            "options": {
                "color": "#FFC107", 
                "lineWidth": 1.5, 
                "lineStyle": 2, 
                "title": atr_label,
                "priceScaleId": 'atrScale',
            }
        })

        # 3.1 RSI
        if show_rsi and 'RSI' in df.columns:
            series.append({
                "type": 'Line',
                "data": [{"time": row[date_col], "value": float(row['RSI'])} for _, row in df.iterrows() if pd.notna(row['RSI'])],
                "options": {
                    "color": '#7E57C2', 
                    "lineWidth": 1.5, 
                    "title": "RSI", 
                    "priceScaleId": 'rsiScale'
                }
            })

        # 3.2 MACD
        if show_macd and 'MACD' in df.columns and 'MACD_Signal' in df.columns:
            macd_data = [{"time": row[date_col], "value": float(row['MACD'])} for _, row in df.iterrows() if pd.notna(row['MACD'])]
            signal_data = [{"time": row[date_col], "value": float(row['MACD_Signal'])} for _, row in df.iterrows() if pd.notna(row['MACD_Signal'])]
            hist_data = [{"time": row[date_col], "value": float(row['MACD'] - row['MACD_Signal']), 
                          "color": 'rgba(38,166,154,0.6)' if float(row['MACD'] - row['MACD_Signal']) >= 0 else 'rgba(239,83,80,0.6)'} 
                         for _, row in df.iterrows() if pd.notna(row['MACD']) and pd.notna(row['MACD_Signal'])]
            
            series.append({
                "type": 'Histogram',
                "data": hist_data,
                "options": {"priceScaleId": 'macdScale', "color": '#26A69A', "title": "MACD Hist"}
            })
            series.append({
                "type": 'Line',
                "data": macd_data,
                "options": {"color": '#2962FF', "lineWidth": 1.5, "title": "MACD", "priceScaleId": 'macdScale'}
            })
            series.append({
                "type": 'Line',
                "data": signal_data,
                "options": {"color": '#FF6D00', "lineWidth": 1.5, "title": "Signal", "priceScaleId": 'macdScale'}
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
                    exact_date_str = pd.to_datetime(past_date).strftime('%m/%d')
                    # check if already in markers to avoid duplicates
                    if not any(m['time'] == closest_date and m['text'].startswith('E') for m in markers):
                        markers.append({
                            "time": closest_date,
                            "position": 'belowBar',
                            "color": '#2196F3',
                            "shape": 'arrowUp',
                            "text": f'E ({exact_date_str})'
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
                    "text": f'E ({pd.to_datetime(analysis.next_earnings_date).strftime("%m/%d")})'
                })
            else:
                closest_date = get_closest_past_trading_day(analysis.next_earnings_date)
                if closest_date:
                    markers.append({
                        "time": closest_date,
                        "position": 'belowBar',
                        "color": '#FF9800',
                        "shape": 'arrowUp',
                        "text": f'E ({pd.to_datetime(analysis.next_earnings_date).strftime("%m/%d")})'
                    })
            
        if getattr(analysis, 'dividend_dates', []):
            for d_date in analysis.dividend_dates:
                closest_date = get_closest_past_trading_day(d_date)
                exact_d_str = pd.to_datetime(d_date).strftime('%m/%d')
                if closest_date and not any(m['time'] == closest_date and m['text'].startswith('D') for m in markers):
                    markers.append({
                        "time": closest_date, "position": 'belowBar', "color": '#9C27B0', "shape": 'circle', "text": f'D ({exact_d_str})'
                    })

        if getattr(analysis, 'insider_buy_dates', []):
            for buy_date in analysis.insider_buy_dates:
                closest_date = get_closest_past_trading_day(buy_date)
                if closest_date and not any(m['time'] == closest_date and 'Insider' in m['text'] for m in markers):
                    markers.append({
                        "time": closest_date, "position": 'aboveBar', "color": '#4CAF50', "shape": 'arrowDown', "text": 'Insider Buy'
                    })

        if getattr(analysis, 'insider_sell_dates', []):
            for sell_date in analysis.insider_sell_dates:
                closest_date = get_closest_past_trading_day(sell_date)
                if closest_date and not any(m['time'] == closest_date and 'Insider' in m['text'] for m in markers):
                    markers.append({
                        "time": closest_date, "position": 'aboveBar', "color": '#F44336', "shape": 'arrowDown', "text": 'Insider Sell'
                    })
                    
        if markers:
            # Find the candlestick series and attach markers to it
            for s in series:
                if s["type"] == 'Candlestick':
                    if "markers" not in s:
                        s["markers"] = markers
                    else:
                        s["markers"].extend(markers)
                    break
            
        series.append(vol_series)
        
        return series

    def generate_candlestick_chart(
        self,
        analysis: StockAnalysis,
        timeframe: str = "W",
        default_range: str = "5Y",
        show_ema: bool = True,
        show_atr: bool = False,
        show_rsi: bool = True,
        show_macd: bool = True,
        show_bollinger: bool = False,
        show_support_resistance: bool = True,
        show_hvn: bool = True,
        show_trade_setup: bool = True,
        show_channel: bool = True,
        user_annotations: list = None,
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
        series_daily = self._build_series(daily_df, date_col, analysis, show_ema, show_atr, show_rsi, show_macd, show_bollinger, show_support_resistance, show_hvn, show_trade_setup, show_channel, user_annotations)
        
        # Determine Weekly Series
        weekly_df = df.copy()
        weekly_df[date_col] = pd.to_datetime(weekly_df[date_col])
        weekly_df.set_index(date_col, inplace=True)
        
        agg_dict = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
        for col in ['EMA20', 'EMA50', 'EMA200', 'ATR', 'ATR_Daily', 'RSI', 'MACD', 'MACD_Signal', 'Bollinger_Upper', 'Bollinger_Lower', 'Trend_Center', 'Trend_Upper', 'Trend_Lower', 'Trend_Std']:
            if col in weekly_df.columns:
                agg_dict[col] = 'last'
                
        weekly_df = weekly_df.resample('W-FRI').agg(agg_dict).dropna(subset=['Open', 'High', 'Low', 'Close']).reset_index()
        weekly_df[date_col] = pd.to_datetime(weekly_df[date_col]).dt.strftime('%Y-%m-%d')
        series_weekly = self._build_series(weekly_df, date_col, analysis, show_ema, show_atr, show_rsi, show_macd, show_bollinger, show_support_resistance, show_hvn, show_trade_setup, show_channel, user_annotations)

        theme = st.session_state.get('theme_preference', 'dark')
        bg_color = '#0E1117' if theme == 'dark' else '#FFFFFF'
        text_color = '#FFFFFF' if theme == 'dark' else '#1E1E1E'
        grid_color = '#1E2229' if theme == 'dark' else '#E0E0E0'

        chartOptions = {
            "layout": { "textColor": text_color, "background": {"type": "solid", "color": bg_color} },
            "grid": { "vertLines": {"color": grid_color, "style": 1}, "horzLines": {"color": grid_color, "style": 1} },
            "crosshair": { "mode": 1 },
            "rightPriceScale": { "borderColor": grid_color, "visible": True, "autoScale": True, "scaleMargins": {"top": 0.10, "bottom": 0.25} },
            "leftPriceScale": { "visible": False },
            "timeScale": { "borderColor": grid_color, "timeVisible": True, "rightOffset": 60 }
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
                        <button class="tvc-tf-btn" data-tf="D">Daily</button>
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
                <div id="tvchart-container" style="position: relative; flex: 1; width: 100%; overflow: hidden;">
                    <div id="tvc-tooltip" style="position: absolute; display: none; padding: 8px; box-sizing: border-box; font-size: 13px; font-family: sans-serif; color: {text_color}; background-color: {bg_color}; opacity: 0.9; z-index: 1000; top: 12px; left: 12px; pointer-events: none; border-radius: 4px; border: 1px solid {grid_color}; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"></div>
                </div>
                <div id="tvchart-volume-container" style="height: 140px; width: 100%; border-top: 2px solid {grid_color}; overflow: hidden;"></div>
            </div>
            <script>
                const script = document.createElement('script');
                script.src = "https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js";
                script.onload = () => {{
                    try {{
                        const chartOptions = {json.dumps(chartOptions)};
                        const chart = LightweightCharts.createChart(document.getElementById('tvchart-container'), chartOptions);
                        
                        const volOptions = JSON.parse(JSON.stringify(chartOptions));
                        const volChart = LightweightCharts.createChart(document.getElementById('tvchart-volume-container'), volOptions);
                        
                        // Sync Zooming across both canvases seamlessly
                        chart.timeScale().subscribeVisibleLogicalRangeChange(range => {{
                            if (range) volChart.timeScale().setVisibleLogicalRange(range);
                        }});
                        volChart.timeScale().subscribeVisibleLogicalRangeChange(range => {{
                            if (range) chart.timeScale().setVisibleLogicalRange(range);
                        }});
                        
                        // Distinct Panes Setup using Scale Margins
                        const hasAtr = {str(show_atr).lower()};
                        const hasRsi = {str(show_rsi).lower()};
                        const hasMacd = {str(show_macd).lower()};
                        
                        const activeSubpanes = [];
                        if (hasAtr) activeSubpanes.push('atrScale');
                        if (hasRsi) activeSubpanes.push('rsiScale');
                        if (hasMacd) activeSubpanes.push('macdScale');
                        
                        const numSubpanes = activeSubpanes.length;
                        const paneHeight = 0.20; // 20% height for each subpane
                        const totalSubpaneHeight = numSubpanes * paneHeight;
                        
                        const mainBottomMargin = Math.min(0.10 + totalSubpaneHeight, 0.85); // buffer for scale minimums
                        
                        chart.priceScale('right').applyOptions({{
                            scaleMargins: {{ top: 0.10, bottom: mainBottomMargin }},
                        }});
                        
                        // Volume has its own native chart space now
                        volChart.priceScale('volScale').applyOptions({{
                            scaleMargins: {{ top: 0.1, bottom: 0.0 }},
                        }});
                        
                        activeSubpanes.forEach((scaleId, index) => {{
                            const startTop = 1.0 - totalSubpaneHeight + (index * paneHeight);
                            chart.priceScale(scaleId).applyOptions({{
                                scaleMargins: {{ top: startTop + 0.02, bottom: 1.0 - (startTop + paneHeight) + 0.02 }},
                                visible: true,
                                borderColor: '{grid_color}',
                            }});
                        }});
                        
                        const datasets = {{
                            "D": {json.dumps(series_daily)},
                            "W": {json.dumps(series_weekly)}
                        }};
                        
                        let seriesInstances = [];
                        let currentTF = "{timeframe}";
                        if (!datasets[currentTF]) currentTF = "W";
                        
                        // Initialization routine
                        function initSeries() {{
                            datasets[currentTF].forEach((s, idx) => {{
                                let inst;
                                let tChart = (s.type === 'Histogram' && s.options.priceScaleId === 'volScale') ? volChart : chart;
                                
                                if (s.type === 'Candlestick') {{
                                    inst = tChart.addCandlestickSeries(s.options);
                                    if (s.priceLines) s.priceLines.forEach(pl => inst.createPriceLine(pl));
                                }} else if (s.type === 'Line') {{
                                    inst = tChart.addLineSeries(s.options);
                                    if (s.priceLines) s.priceLines.forEach(pl => inst.createPriceLine(pl));
                                }} else if (s.type === 'Histogram') {{
                                    inst = tChart.addHistogramSeries(s.options);
                                }}
                                seriesInstances.push({{ inst: inst, parent: tChart }});
                            }});
                        }}
                        
                        function applyData(tf) {{
                            datasets[tf].forEach((s, idx) => {{
                                seriesInstances[idx].inst.setData(s.data);
                                if (s.type === 'Candlestick' || s.type === 'Histogram') {{
                                    if (s.markers) seriesInstances[idx].inst.setMarkers(s.markers);
                                    else seriesInstances[idx].inst.setMarkers([]); // clear explicit empty markers
                                }}
                            }});
                        }}
                        
                        initSeries();
                        applyData(currentTF);
                        
                        // Interactive Tooltip
                        const tooltip = document.getElementById('tvc-tooltip');
                        
                        chart.subscribeCrosshairMove(param => {{
                            if (
                                param.point === undefined ||
                                !param.time ||
                                param.point.x < 0 ||
                                param.point.x > document.getElementById('tvchart-container').clientWidth ||
                                param.point.y < 0 ||
                                param.point.y > document.getElementById('tvchart-container').clientHeight
                            ) {{
                                tooltip.style.display = 'none';
                                return;
                            }}
                            
                            // Get candle data
                            const data = param.seriesData.get(seriesInstances[0].inst);
                            if (!data) {{
                                tooltip.style.display = 'none';
                                return;
                            }}
                            
                            // Format date
                            const dateStr = typeof param.time === 'string' ? param.time : new Date(param.time * 1000).toLocaleDateString({{ month: 'short', day: 'numeric', year: 'numeric' }});
                            
                            // Set tooltip content
                            tooltip.innerHTML = `
                                <div style="font-weight: bold; margin-bottom: 4px;">${{dateStr}}</div>
                                <div>O: <span style="color: ${{data.open < data.close ? '#26a69a' : '#ef5350'}}">${{data.open.toFixed(2)}}</span></div>
                                <div>H: <span style="color: ${{data.open < data.close ? '#26a69a' : '#ef5350'}}">${{data.high.toFixed(2)}}</span></div>
                                <div>L: <span style="color: ${{data.open < data.close ? '#26a69a' : '#ef5350'}}">${{data.low.toFixed(2)}}</span></div>
                                <div>C: <span style="color: ${{data.open < data.close ? '#26a69a' : '#ef5350'}}">${{data.close.toFixed(2)}}</span></div>
                            `;
                            
                            // Position tooltip dynamically
                            const y = param.point.y;
                            
                            let left = param.point.x + 15;
                            if (left > document.getElementById('tvchart-container').clientWidth - 100) {{
                                left = param.point.x - 105;
                            }}
                            
                            let top = y + 15;
                            if (top > document.getElementById('tvchart-container').clientHeight - 100) {{
                                top = y - 105;
                            }}
                            
                            tooltip.style.left = left + 'px';
                            tooltip.style.top = top + 'px';
                            tooltip.style.display = 'block';
                        }});
                        
                        // Set active toggle visually based on python prop
                        document.querySelectorAll('.tvc-tf-btn').forEach(btn => {{
                            btn.classList.remove('active');
                            if(btn.getAttribute('data-tf') === currentTF) btn.classList.add('active');
                        }});
                        
                        // Apply Default Range Zoom
                        setTimeout(() => {{
                            const defaultZoomBtn = document.querySelector(`.tvc-btn[data-range="{default_range}"]`);
                            if(defaultZoomBtn) defaultZoomBtn.click();
                        }}, 50);

                        // Resize observer
                        new ResizeObserver(entries => {{
                          entries.forEach(entry => {{
                              if (entry.target.id === 'tvchart-container') {{
                                  chart.applyOptions({{ width: entry.contentRect.width, height: entry.contentRect.height }});
                              }}
                          }});
                        }}).observe(document.getElementById('tvchart-container'));
                        
                        new ResizeObserver(entries => {{
                          entries.forEach(entry => {{
                              if (entry.target.id === 'tvchart-volume-container') {{
                                  volChart.applyOptions({{ width: entry.contentRect.width, height: entry.contentRect.height }});
                              }}
                          }});
                        }}).observe(document.getElementById('tvchart-volume-container'));
                        
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
                                
                                // Find the candlestick series dynamically instead of hardcoding [0]
                                let totalData = [];
                                datasets[currentTF].forEach(s => {{
                                    if(s.type === 'Candlestick') {{
                                        totalData = s.data;
                                    }}
                                }});
                                
                                if(totalData.length === 0) return;
                                
                                // Safe date parsing for Safari/WebKit
                                function parseDateSafe(dateStr) {{
                                    if (!dateStr) return new Date();
                                    // Handle 'YYYY-MM-DD' strictly avoiding timezone shift parsing bugs
                                    if (dateStr.includes('-')) {{
                                        const parts = dateStr.split('-');
                                        return new Date(parts[0], parts[1] - 1, parts[2]);
                                    }}
                                    return new Date(dateStr);
                                }}
                                
                                const lastDateStr = totalData[totalData.length - 1].time;
                                const lastDate = parseDateSafe(lastDateStr);
                                let fromDate = new Date(lastDate.getTime());
                                
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
                                    if(parseDateSafe(totalData[i].time) >= fromDate) {{
                                        closestIdx = i;
                                        break;
                                    }}
                                }}
                                
                                // Safe zoom without relying on uninitialized pixel coordinates
                                chart.timeScale().setVisibleLogicalRange({{
                                    from: closestIdx,
                                    to: totalData.length + 5
                                }});
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
