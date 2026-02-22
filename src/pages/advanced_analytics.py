"""Advanced analytics page for Streamlit dashboard"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import asyncio
from datetime import datetime
from src.analyzer import StockAnalyzer
from src.data_sources.options_source import OptionsSource
from src.data_sources.insider_source import InsiderSource
from src.data_sources.institutional_source import InstitutionalSource
from src.data_sources.short_interest_source import ShortInterestSource
from src.data_sources.news_source import NewsSentimentSource
from src.data_sources.earnings_source import EarningsSource
from src.pattern_recognition import PatternRecognition
from src.visualization_advanced import AdvancedVisualizations
from src.options_calc import OptionsProfitCalculator
from src.math_models import MonteCarloEngine
from src.utils import render_ticker_header, save_analysis
from src.valuations import ValuationCalculator
from src.reporting import ReportGenerator


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
            whale_source = InstitutionalSource()
            short_source = ShortInterestSource()
            news_source = NewsSentimentSource()
            earn_source = EarningsSource()
            
            # Get basic analysis
            analysis = asyncio.run(analyzer.analyze(ticker))
            
            if analysis:
                # Save to database
                db = st.session_state.get('db')
                if db:
                    save_analysis(db, analysis)
                
                from src.ai_analyzer import AIAnalyzer
                
                # Render shared header
                render_ticker_header(analysis)
                
                user_tier = st.session_state.get('tier', 'free')
                if user_tier != 'free':
                    # --- AI Thesis Generation Block ---
                    st.markdown("---")
                    col_ai1, col_ai2 = st.columns([3, 1])
                    with col_ai1:
                        st.subheader("🤖 AI-Powered Trade Thesis")
                        st.caption("Powered by Google Gemini")
                    
                    with col_ai2:
                        if st.button("✨ Generate AI Thesis", use_container_width=True):
                            with st.spinner("Synthesizing market data..."):
                                ai = AIAnalyzer()
                                
                                # Construct unified data payload from existing analysis objects
                                payload = {
                                    "current_price": analysis.current_price,
                                    "trend": "Bullish" if analysis.current_price > getattr(analysis, 'sma_50', 0) else "Bearish",
                                    "support": getattr(analysis, 'support_level', "N/A"),
                                    "resistance": getattr(analysis, 'resistance_level', "N/A")
                                }
                                
                                # Safely attempt to pull extended metrics if available
                                try:
                                    opt_data = asyncio.run(options_source.fetch_data(ticker))
                                    if opt_data and 'max_pain' in opt_data:
                                        payload['hvn'] = opt_data['max_pain']
                                except Exception:
                                    pass
                                    
                                try:
                                    sent_data = news_source.get_sentiment(ticker)
                                    if sent_data:
                                        payload['sentiment'] = sent_data
                                except Exception:
                                    pass
                                    
                                try:
                                    earn_data = asyncio.run(earn_source.fetch_data(ticker))
                                    if earn_data and not earn_data.empty:
                                        payload['earnings'] = {'drift_direction': earn_data.iloc[0].get('drift_direction', 'Unknown')}
                                except Exception:
                                    pass
                                    
                                thesis = ai.generate_thesis(ticker, payload)
                                
                                st.info(thesis)
                    st.markdown("---")
                    # ----------------------------------
                
                # Display tabs
                tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
                    "🎲 Monte Carlo",
                    "📰 News Sentiment",
                    "📅 Earnings Drift",
                    "📊 Options Data",
                    "👔 Insider Trading",
                    "🐋 Whale Tracking",
                    "📉 Short Interest",
                    "🕯️ Patterns",
                    "💰 Valuations"
                ])
                
                # Tab 1: Monte Carlo Probabilities
                with tab1:
                    st.subheader("10,000-Path Monte Carlo Price Simulation")
                    st.markdown("Projects future price probabilities based on stock's historical volatility and daily returns (Geometric Brownian Motion).")
                    
                    if analysis.history is not None and not analysis.history.empty:
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            days_out = st.slider("Days to Simulate", min_value=14, max_value=90, value=30, step=7)
                        
                        with col2:
                            num_sims = st.selectbox("Number of Simulations", options=[1000, 5000, 10000], index=2)
                        
                        with st.spinner(f"Running {num_sims:,} simulations..."):
                            mc_results = MonteCarloEngine.simulate_gbm(
                                current_price=analysis.current_price,
                                history=analysis.history,
                                days_out=days_out,
                                num_simulations=num_sims
                            )
                            
                        if mc_results:
                            
                            mc_fig = go.Figure()
                            
                            # We don't want to draw 10,000 lines (too heavy for browser)
                            # Let's draw 100 random sample paths in light grey
                            paths = mc_results['paths']
                            sample_indices = np.random.choice(paths.shape[1], size=min(100, paths.shape[1]), replace=False)
                            
                            x_axis = np.arange(days_out + 1)
                            
                            # Add sample lines
                            for idx in sample_indices:
                                mc_fig.add_trace(go.Scatter(
                                    x=x_axis, y=paths[:, idx],
                                    mode='lines',
                                    line=dict(color='rgba(150, 150, 150, 0.1)', width=1),
                                    showlegend=False,
                                    hoverinfo='skip'
                                ))
                                
                            # Calculate percentiles across all paths
                            p5_path = np.percentile(paths, 5, axis=1)
                            p50_path = np.percentile(paths, 50, axis=1)
                            p95_path = np.percentile(paths, 95, axis=1)
                            
                            # Add Confidence Interval Cone (90% Confidence)
                            mc_fig.add_trace(go.Scatter(
                                x=np.concatenate([x_axis, x_axis[::-1]]),
                                y=np.concatenate([p95_path, p5_path[::-1]]),
                                fill='toself',
                                fillcolor='rgba(0, 100, 250, 0.2)',
                                line=dict(color='rgba(255,255,255,0)'),
                                hoverinfo="skip",
                                name="90% Confidence Interval"
                            ))
                            
                            # Add Median line
                            mc_fig.add_trace(go.Scatter(
                                x=x_axis, y=p50_path,
                                mode='lines',
                                line=dict(color='rgb(50, 150, 250)', width=3, dash='dash'),
                                name="Expected Path (Median)"
                            ))
                            
                            mc_fig.update_layout(
                                title=f"Price Projection Cone ({days_out} Days)",
                                xaxis_title="Trading Days from Today",
                                yaxis_title="Price ($)",
                                height=450,
                                showlegend=True,
                                margin=dict(l=20, r=20, t=40, b=20)
                            )
                            st.plotly_chart(mc_fig, use_container_width=True)
                            
                            # Display exact probability metrics
                            st.markdown("### Probable Outcomes")
                            p_cols = st.columns(4)
                            p_cols[0].metric("Target Price (Median)", f"${mc_results['percentiles']['p50']:.2f}")
                            p_cols[1].metric("Bull Case (Top 5%)", f"${mc_results['percentiles']['p95']:.2f}")
                            p_cols[2].metric("Bear Case (Bottom 5%)", f"${mc_results['percentiles']['p5']:.2f}")
                            
                            prob_up = mc_results['prob_higher'] * 100
                            p_cols[3].metric("Win Probability", f"{prob_up:.1f}%")
                            
                    else:
                        st.error("Missing historical price data required for simulation.")
                        
                # Tab 2: News Sentiment Heatmap
                with tab2:
                    st.subheader("📰 Local News Sentiment Analyzer")
                    st.markdown("Scans recent headlines using Natural Language Processing (TextBlob) to detect media shifts before price reacts.")
                    
                    with st.spinner("Analyzing recent news..."):
                        news_data = news_source.fetch_and_analyze_news(ticker, max_articles=20)
                        
                    if news_data and news_data['articles']:
                        avg_sent = news_data['average_sentiment']
                        label = news_data['sentiment_label']
                        
                        # Overall metrics
                        ncol1, ncol2, ncol3 = st.columns(3)
                        ncol1.metric("Average Sentiment Score", f"{avg_sent:.3f}", 
                                     f"{avg_sent*100:.1f}%" if avg_sent != 0 else None,
                                     delta_color="normal" if avg_sent > 0 else "inverse" if avg_sent < 0 else "off")
                        ncol2.metric("Overall Bias", label)
                        ncol3.metric("Articles Analyzed", len(news_data['articles']))
                        
                        if news_data and 'articles' in news_data and len(news_data['articles']) > 0:
                        
                            news_df = pd.DataFrame(news_data['articles'])
                            # Reverse so newest is on the right
                            news_df = news_df.iloc[::-1].reset_index(drop=True)
                            
                            colors = ['#00C851' if s > 0.1 else '#ff4444' if s < -0.1 else '#33b5e5' for s in news_df['sentiment_score']]
                            
                            fig_news = go.Figure(data=[
                                go.Bar(
                                    x=news_df.index,
                                    y=news_df['sentiment_score'],
                                    marker_color=colors,
                                    text=news_df['sentiment_label'],
                                    hovertext=news_df['title'] + '<br>' + news_df['date'],
                                    hoverinfo="text"
                                )
                            ])
                            
                            fig_news.update_layout(
                                title="Recent Headline Sentiment Scores",
                                xaxis_title="Article Flow (Oldest to Newest)",
                                yaxis_title="NLP Polarity (-1 to 1)",
                                xaxis=dict(showticklabels=False), # Hide indices
                                yaxis=dict(range=[-1.1, 1.1]),
                                height=300,
                                margin=dict(l=20, r=20, t=40, b=20)
                            )
                            # Add a zero line
                            fig_news.add_hline(y=0, line_width=1, line_color="white")
                            
                            st.plotly_chart(fig_news, use_container_width=True)
                            
                            st.markdown("### Latest Headlines")
                            for idx, row in news_df.iloc[::-1].iterrows(): # Show newest first here
                                emoji = "🟢" if row['sentiment_label'] == "Bullish" else "🔴" if row['sentiment_label'] == "Bearish" else "⚪"
                                st.markdown(f"**{emoji} [{row['title']}]({row['link']})**")
                                st.caption(f"{row['publisher']} • {row['date']} • Score: {row['sentiment_score']:.3f} ")
                                st.divider()
                    else:
                        st.warning("No recent news found to analyze.")
                        
                # Tab 3: Earnings Drift Analyzer
                with tab3:
                    st.subheader("📅 Post-Earnings Price Drift")
                    st.markdown("Statistically analyzes how this stock behaves on the day after (T+1) and two weeks after (T+14) earnings reports.")
                    
                    with st.spinner("Fetching historical earnings data..."):
                        earn_data = earn_source.fetch_earnings_drift(ticker, limit=12)
                        
                    if earn_data and earn_data['analyzed_events'] > 0:
                        
                        ecol1, ecol2, ecol3 = st.columns(3)
                        ecol1.metric("Historical Win Rate (T+14)", f"{earn_data['win_rate_t14_pct']:.1f}%")
                        ecol2.metric("Average T+1 Day Move", f"{earn_data['avg_t1_return']:+.2f}%", 
                                     delta_color="normal" if earn_data['avg_t1_return'] > 0 else "inverse")
                        ecol3.metric("Average T+14 Day Drift", f"{earn_data['avg_t14_return']:+.2f}%",
                                     delta_color="normal" if earn_data['avg_t14_return'] > 0 else "inverse")
                                     
                        st.markdown("### Historical Earnings Events")
                        
                        # Format as DataFrame
                        edf = pd.DataFrame(earn_data['events'])
                        
                        # Add a visual emoji for Beats vs Miss
                        def format_beat(val):
                            if pd.isna(val): return "Unknown"
                            return "✅ Beat" if val else "❌ Miss"
                            
                        edf['beat_status'] = edf['beat'].apply(format_beat)
                        
                        # Reorder and rename columns for display
                        display_df = edf[['date', 'eps_estimate', 'eps_reported', 'beat_status', 't0_return', 't1_return', 't14_return']].copy()
                        display_df.columns = ['Date', 'Est EPS', 'Reported EPS', 'Status', 'Closing Impact (T0)', 'Next Day Drift (T+1)', '2-Week Drift (T+14)']
                        
                        # Apply a background gradient to returns
                        formatted_edf = display_df.style.format({
                            'Est EPS': '${:.2f}',
                            'Reported EPS': '${:.2f}',
                            'Closing Impact (T0)': '{:+.2f}%',
                            'Next Day Drift (T+1)': '{:+.2f}%',
                            '2-Week Drift (T+14)': '{:+.2f}%'
                        }).background_gradient(
                            cmap='RdYlGn', 
                            subset=['Closing Impact (T0)', 'Next Day Drift (T+1)', '2-Week Drift (T+14)'], 
                            vmin=-15, vmax=15
                        )
                        
                        st.dataframe(formatted_edf, use_container_width=True)
                        
                    else:
                        st.warning("Insufficient historical earnings data to analyze drift.")
                        
                # Tab 4: Options Data
                with tab4:
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

                        # Options P/L Curve
                        if analysis.suggested_entry and iv > 0:
                            st.divider()
                            st.subheader("🧪 Theoretical Options Strategy")
                            st.markdown("Based on current IV and the algorithmic **Suggested Entry**.")
                            
                            target_price = analysis.max_buy_price if analysis.max_buy_price else (analysis.suggested_entry * 1.15)
                            
                            pl_data = OptionsProfitCalculator.generate_pl_curve(
                                entry_price=analysis.suggested_entry,
                                target_price=target_price,
                                current_iv=iv,
                                days_to_exp=45
                            )
                            
                            st.markdown(f"**Recommended Action:** Buy 1 Call Contract at **${pl_data['suggested_strike']} Strike** expiring in ~45 Days.")
                            # Chart the P/L
                            pl_fig = go.Figure()
                            # Find indices where profit > 0 to color green vs red
                            pl_fig.add_trace(go.Scatter(
                                x=pl_data['curve_prices'],
                                y=pl_data['curve_profit_loss'],
                                mode='lines',
                                name="P/L ($)",
                                line=dict(color='rgba(150, 150, 250, 0.8)', width=3),
                                fill='tozeroy'
                            ))
                            
                            # Add vertical line for entry
                            pl_fig.add_vline(x=analysis.suggested_entry, line_width=2, line_dash="dash", line_color="orange", annotation_text="Entry")
                            
                            # Target horizontal zero line
                            pl_fig.add_hline(y=0, line_width=1, line_color="white")
                            
                            pl_fig.update_layout(
                                title="Theoretical Profit / Loss at Expiration",
                                xaxis_title="Underlying Stock Price ($)",
                                yaxis_title="Profit/Loss ($)",
                                height=350,
                                margin=dict(l=20, r=20, t=40, b=20)
                            )
                            st.plotly_chart(pl_fig, use_container_width=True)
                            
                    else:
                        st.warning("No options data available for this ticker")
                
                # Tab 5: Insider Trading
                with tab5:
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
                
                # Tab 6: Whale Tracking
                with tab6:
                    st.subheader("Major Institutional Holders")
                    
                    with st.spinner("Fetching institutional holdings..."):
                        whale_data = whale_source.fetch_institutional_holders(ticker)
                    
                    if whale_data:
                        breakdown = whale_data.get('major_holdings_breakdown', {})
                        if breakdown:
                            st.write("**Holdings Breakdown**")
                            b_cols = st.columns(min(len(breakdown), 4))
                            for i, (desc, val) in enumerate(breakdown.items()):
                                col = b_cols[i % 4]
                                # If it looks like a percentage string or float
                                if isinstance(val, float):
                                    if val < 2.0: # likely a raw decimal like 0.65
                                        disp_val = f"{val:.2%}"
                                    else:
                                        disp_val = f"{val:,.0f}"
                                else:
                                    disp_val = str(val)
                                col.metric(desc, disp_val)
                            
                        st.markdown("---")
                        
                        wcol1, wcol2 = st.columns(2)
                        
                        with wcol1:
                            st.write("**Top Mutual Fund Holders**")
                            mut_df = pd.DataFrame(whale_data.get("mutualfund_holders", []))
                            if not mut_df.empty:
                                st.dataframe(mut_df[['holder', 'shares', 'value', 'date_reported']].style.format({
                                    'shares': '{:,}',
                                    'value': '${:,.0f}'
                                }), use_container_width=True)
                            else:
                                st.info("No mutual fund data available.")
                                
                        with wcol2:
                            st.write("**Top Institutional Holders**")
                            inst_df = pd.DataFrame(whale_data.get("institutional_holders", []))
                            if not inst_df.empty:
                                st.dataframe(inst_df[['holder', 'shares', 'value', 'date_reported']].style.format({
                                    'shares': '{:,}',
                                    'value': '${:,.0f}'
                                }), use_container_width=True)
                            else:
                                st.info("No institutional data available.")
                    else:
                        st.warning("No institutional data available for this ticker.")
                
                # Tab 7: Short Interest
                with tab7:
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
                
                # Tab 8: Candlestick Patterns
                with tab8:
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
                
                # Tab 9: Valuations
                with tab9:
                    st.subheader("Intrinsic Value Estimates")
                    
                    calc = ValuationCalculator()
                    graham = calc.calculate_graham_number(analysis)
                    dcf = calc.calculate_dcf(analysis)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Graham Number", f"${graham:.2f}" if graham else "N/A", help="sqrt(22.5 * EPS * Book Value)")
                        if graham and analysis.current_price:
                            upside = (graham / analysis.current_price) - 1
                            st.caption(f"Upside/Downside: {upside:+.1%}")
                            
                    with col2:
                        intrinsic = dcf.get('intrinsic_value') if dcf else None
                        st.metric("DCF Intrinsic Value", f"${intrinsic:.2f}" if intrinsic else "N/A", help="5-year projected FCF with 10% discount rate")
                        if intrinsic and analysis.current_price:
                            upside = (intrinsic / analysis.current_price) - 1
                            st.caption(f"Upside/Downside: {upside:+.1%}")
                    
                    st.divider()
                    
                    if dcf:
                        st.write("**DCF Assumptions:**")
                        st.write(f"- Growth Rate: {dcf['growth_rate_used']:.1%}")
                        st.write(f"- Discount Rate: {dcf['discount_rate_used']:.1%}")
                        
                        # Project FCF chart
                        st.write("**Projected Free Cash Flow (5 Years):**")
                        fcf_df = pd.DataFrame({
                            'Year': [f"Year {i+1}" for i in range(len(dcf['projected_fcf']))],
                            'FCF ($)': dcf['projected_fcf']
                        })
                        st.line_chart(fcf_df.set_index('Year'))
                    
                    st.divider()
                    st.subheader("Data Transparency")
                    if analysis.analyst_source:
                        st.info(f"📍 **Analyst Target Source:** {analysis.analyst_source}")
                    else:
                        st.warning("No analyst source metadata available.")

                    # Professional Export
                    st.subheader("📑 Professional Reporting")
                    excel_data = ReportGenerator.generate_excel_report(analysis, dcf)
                    st.download_button(
                        label="📥 Download Detailed Excel Analysis",
                        data=excel_data,
                        file_name=f"{analysis.ticker}_analysis_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            else:
                st.error(f"Failed to analyze {ticker}. Please check the ticker symbol.")


if __name__ == "__main__":
    render_advanced_analytics_page()
