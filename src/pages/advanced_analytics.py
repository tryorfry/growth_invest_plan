"""Advanced analytics page for Streamlit dashboard"""

import streamlit as st
import pandas as pd
import asyncio
from src.analyzer import StockAnalyzer
from src.data_sources.options_source import OptionsSource
from src.data_sources.insider_source import InsiderSource
from src.data_sources.short_interest_source import ShortInterestSource
from src.pattern_recognition import PatternRecognition
from src.visualization_advanced import AdvancedVisualizations
from src.utils import render_ticker_header, save_analysis


def render_candlestick_icon(pattern_type: str):
    """Render a compact SVG-based candlestick icon for a table row"""
    p_type = pattern_type.lower()
    
    # Colors
    bull_color = "#2ecc71"
    bear_color = "#e74c3c"
    neutral_color = "#aaa"
    
    # Canvas
    svg = '<svg width="40" height="50" viewBox="0 0 40 50" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle;">'
    
    if 'doji' in p_type:
        # Doji: Long wick, thin body in middle
        svg += f'<line x1="20" y1="5" x2="20" y2="45" stroke="{neutral_color}" stroke-width="2" />'
        svg += f'<line x1="12" y1="25" x2="28" y2="25" stroke="white" stroke-width="2" />'
    
    elif 'hammer' in p_type:
        # Hammer: Long lower wick, small body at top
        svg += f'<line x1="20" y1="10" x2="20" y2="45" stroke="{bull_color}" stroke-width="2" />'
        svg += f'<rect x="12" y="10" width="16" height="10" fill="{bull_color}" />'
    
    elif 'shooting star' in p_type:
        # Shooting Star: Long upper wick, small body at bottom
        svg += f'<line x1="20" y1="5" x2="20" y2="40" stroke="{bear_color}" stroke-width="2" />'
        svg += f'<rect x="12" y="30" width="16" height="10" fill="{bear_color}" />'
    
    elif 'bullish' in p_type and 'engulfing' in p_type:
        # Two candles: Small red, large green
        svg += f'<rect x="8" y="25" width="8" height="15" fill="{bear_color}" />'
        svg += f'<rect x="24" y="10" width="10" height="35" fill="{bull_color}" />'
    
    elif 'bearish' in p_type and 'engulfing' in p_type:
        # Two candles: Small green, large red
        svg += f'<rect x="8" y="25" width="8" height="15" fill="{bull_color}" />'
        svg += f'<rect x="24" y="10" width="10" height="35" fill="{bear_color}" />'
    
    else:
        # Generic candle for unknown
        svg += f'<line x1="20" y1="5" x2="20" y2="45" stroke="{neutral_color}" stroke-width="2" />'
        svg += f'<rect x="14" y="15" width="12" height="20" fill="{neutral_color}" />'
        
    svg += '</svg>'
    return svg


def render_advanced_analytics_page():
    """Render the advanced analytics page"""
    st.title("🔬 Advanced Analytics")
    
    # Sidebar integration for history
    with st.sidebar:
        st.divider()
        st.subheader("Search History")
        db = st.session_state.get('db')
        default_ticker = "AAPL"
        if db:
            db_tickers = db.get_all_tickers()
            if db_tickers:
                selected_history = st.selectbox(
                    "Recent Tickers",
                    options=["Enter New..."] + db_tickers,
                    index=0,
                    key="adv_history"
                )
                if selected_history != "Enter New...":
                    default_ticker = selected_history

    # Ticker input
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker = st.text_input("Enter Stock Ticker", value=default_ticker).upper()
    with col2:
        st.write("") # Alignment
        analyze_btn = st.button("Analyze", type="primary", use_container_width=True)
    
    if analyze_btn and ticker:
        with st.spinner(f"Analyzing {ticker}..."):
            # Initialize sources
            analyzer = StockAnalyzer()
            options_source = OptionsSource()
            insider_source = InsiderSource()
            short_source = ShortInterestSource()
            
            # Get basic analysis
            analysis = asyncio.run(analyzer.analyze(ticker))
            
            if analysis:
                # Save to database
                db = st.session_state.get('db')
                if db:
                    save_analysis(db, analysis)
                
                # Render shared header
                render_ticker_header(analysis)
                
                # Display tabs
                tab1, tab2, tab3, tab4 = st.tabs([
                    "📊 Options Data",
                    "👔 Insider Trading",
                    "📉 Short Interest",
                    "🕯️ Patterns"
                ])
                
                # Tab 1: Options Data
                with tab1:
                    st.subheader("Options Metrics")
                    
                    options_data = options_source.fetch_options_data(ticker)
                    
                    if options_data:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            iv = options_data.get('implied_volatility', 0)
                            st.metric(
                                "Implied Volatility",
                                f"{iv:.2%}" if iv else "N/A",
                                help="Average IV of at-the-money options"
                            )
                        
                        with col2:
                            pcr = options_data.get('put_call_ratio', 0)
                            st.metric(
                                "Put/Call Ratio",
                                f"{pcr:.2f}" if pcr else "N/A",
                                help="Ratio of put volume to call volume"
                            )
                        
                        with col3:
                            exp = options_data.get('nearest_expiration', 'N/A')
                            st.metric(
                                "Nearest Expiration",
                                exp,
                                help="Nearest options expiration date"
                            )
                        
                        st.markdown("---")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            call_vol = options_data.get('total_call_volume', 0)
                            st.metric("Total Call Volume", f"{call_vol:,}")
                        with col2:
                            put_vol = options_data.get('total_put_volume', 0)
                            st.metric("Total Put Volume", f"{put_vol:,}")
                        
                        # Interpretation
                        st.markdown("### Interpretation")
                        if pcr > 1:
                            st.info("📉 Put/Call Ratio > 1: More puts than calls, potentially bearish sentiment")
                        elif pcr < 0.7:
                            st.info("📈 Put/Call Ratio < 0.7: More calls than puts, potentially bullish sentiment")
                        else:
                            st.info("➡️ Put/Call Ratio neutral")
                    else:
                        st.warning("No options data available for this ticker")
                
                # Tab 2: Insider Trading
                with tab2:
                    st.subheader("Insider Trading Activity")
                    
                    insider_data = asyncio.run(insider_source.fetch_insider_data(ticker))
                    
                    if insider_data:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            ownership = insider_data.get('insider_ownership_pct', 0)
                            st.metric(
                                "Insider Ownership",
                                f"{ownership:.2f}%",
                                help="Percentage of shares held by insiders"
                            )
                        
                        with col2:
                            txns = insider_data.get('recent_transactions', 0)
                            st.metric(
                                "Recent Transactions",
                                txns,
                                help="Number of recent insider transactions"
                            )
                        
                        with col3:
                            net = insider_data.get('net_insider_activity', 0)
                            delta_color = "normal" if net >= 0 else "inverse"
                            st.metric(
                                "Net Activity",
                                f"{net:,} shares",
                                delta=f"{'Buying' if net > 0 else 'Selling' if net < 0 else 'Neutral'}",
                                delta_color=delta_color,
                                help="Net shares bought minus sold"
                            )
                        
                        # Transactions table
                        if insider_data.get('transactions'):
                            st.markdown("### Recent Transactions")
                            df = pd.DataFrame(insider_data['transactions'])
                            st.dataframe(df, width='stretch')
                        
                        # Interpretation
                        st.markdown("### Interpretation")
                        if net > 0:
                            st.success("✅ Net insider buying - potentially bullish signal")
                        elif net < 0:
                            st.warning("⚠️ Net insider selling - potentially bearish signal")
                        else:
                            st.info("➡️ No significant insider activity")
                    else:
                        st.warning("No insider trading data available")
                
                # Tab 3: Short Interest
                with tab3:
                    st.subheader("Short Interest Metrics")
                    
                    short_data = short_source.fetch_short_interest(ticker)
                    
                    if short_data:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            short_pct = short_data.get('short_percent_of_float', 0)
                            st.metric(
                                "Short % of Float",
                                f"{short_pct:.2f}%",
                                help="Percentage of float shares sold short"
                            )
                        
                        with col2:
                            days_to_cover = short_data.get('short_ratio', 0)
                            st.metric(
                                "Days to Cover",
                                f"{days_to_cover:.2f}",
                                help="Days to cover all short positions at average volume"
                            )
                        
                        with col3:
                            change = short_data.get('short_interest_change_pct', 0)
                            st.metric(
                                "Monthly Change",
                                f"{change:+.2f}%",
                                delta=f"{'Increasing' if change > 0 else 'Decreasing' if change < 0 else 'Flat'}",
                                help="Change in short interest vs. prior month"
                            )
                        
                        st.markdown("---")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            shares = short_data.get('shares_short', 0)
                            st.metric("Shares Short", f"{shares:,}")
                        with col2:
                            prior = short_data.get('shares_short_prior_month', 0)
                            st.metric("Prior Month", f"{prior:,}")
                        
                        # Interpretation
                        st.markdown("### Interpretation")
                        if short_pct > 20:
                            st.warning("⚠️ High short interest (>20%) - potential short squeeze risk")
                        elif short_pct > 10:
                            st.info("📊 Moderate short interest (10-20%)")
                        else:
                            st.success("✅ Low short interest (<10%)")
                    else:
                        st.warning("No short interest data available")
                
                # Tab 4: Candlestick Patterns
                with tab4:
                    if analysis.history is not None and not analysis.history.empty:
                        pattern_detector = PatternRecognition()
                        patterns = pattern_detector.get_recent_patterns(analysis.history, days=30)
                        
                        if patterns:
                            # Build HTML table for patterns
                            table_html = '<div style="overflow-x: auto;"><table style="width: 100%; border-collapse: collapse; margin-top: 10px; color: white; background-color: #0e1117;">'
                            table_html += '<thead><tr style="border-bottom: 2px solid #555; text-align: left;">'
                            table_html += '<th style="padding: 12px; width: 50px;">Icon</th>'
                            table_html += '<th style="padding: 12px;">Date</th>'
                            table_html += '<th style="padding: 12px;">Pattern</th>'
                            table_html += '<th style="padding: 12px;">Signal</th>'
                            table_html += '<th style="padding: 12px;">Price</th></tr></thead><tbody>'
                            
                            for p in patterns:
                                icon_svg = render_candlestick_icon(p["pattern"])
                                row_html = f'<tr style="border-bottom: 1px solid #444;">'
                                row_html += f'<td style="padding: 5px;">{icon_svg}</td>'
                                row_html += f'<td style="padding: 12px; vertical-align: middle;">{p["date"].strftime("%Y-%m-%d")}</td>'
                                row_html += f'<td style="padding: 12px; vertical-align: middle;"><strong style="color: #64b5f6;">{p["pattern"]}</strong></td>'
                                row_html += f'<td style="padding: 12px; vertical-align: middle;">{p["signal"]}</td>'
                                row_html += f'<td style="padding: 12px; vertical-align: middle;">${p["price"]:.2f}</td></tr>'
                                table_html += row_html
                            
                            table_html += '</tbody></table></div>'
                            st.markdown(table_html, unsafe_allow_html=True)
                        else:
                            st.info("No significant candlestick patterns detected in the last 30 days.")
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("""
                        **Quick Definitions:**
                        - **Doji**: Indecision / Neutral
                        - **Hammer**: Bullish Reversal
                        - **Shooting Star**: Bearish Reversal
                        - **Engulfing**: Strong Momentum Reversal
                        """)
                    else:
                        st.error("No historical data available for pattern recognition")
            else:
                st.error(f"Failed to analyze {ticker}. Please check the ticker symbol.")


if __name__ == "__main__":
    render_advanced_analytics_page()
