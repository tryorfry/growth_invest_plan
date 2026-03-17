import streamlit as st
import asyncio
import pandas as pd
from typing import Dict, Any, Optional, List, Union
from src.analyzer import StockAnalysis

def render_multi_style_report(data: Union[StockAnalysis, List[StockAnalysis]]):
    """
    Renders a beautiful comparison report of all trading styles.
    Supports single or multiple tickers.
    """
    if not data:
        st.warning("No multi-style data available. Run the analysis first.")
        return

    # Normalize to list
    analyses = [data] if isinstance(data, StockAnalysis) else data
    
    if not analyses:
        st.warning("No valid analysis results to display.")
        return

    # 1. Summary Leaderboard (if multi-ticker)
    if len(analyses) > 1:
        st.subheader("🏆 Multi-Ticker Opportunity Leaderboard")
        leaderboard_data = []
        for analysis in analyses:
            if analysis.best_style:
                best = analysis.style_results[analysis.best_style]
                leaderboard_data.append({
                    "Ticker": analysis.ticker,
                    "Best Strategy": analysis.best_style,
                    "Setup Quality": f"{best['score']:.0%}",
                    "Trend": best['trend'],
                    "R/R": f"{best['rr']:.1f}x",
                    "Target Upside": f"{((best['target']-analysis.current_price)/analysis.current_price)*100:+.1f}%" if best['target'] and analysis.current_price else "N/A"
                })
        
        if leaderboard_data:
            df_leader = pd.DataFrame(leaderboard_data)
            # Sort by Setup Quality (descending)
            df_leader['SortOrder'] = df_leader['Setup Quality'].str.rstrip('%').astype(float)
            df_leader = df_leader.sort_values('SortOrder', ascending=False).drop(columns=['SortOrder'])
            st.dataframe(df_leader, use_container_width=True, hide_index=True)
        st.divider()

    # 2. Detailed Ticker Tabs
    if len(analyses) == 1:
        _render_single_ticker_report(analyses[0], show_header=True)
    else:
        tabs = st.tabs([f"📊 {a.ticker}" for a in analyses])
        for i, analysis in enumerate(analyses):
            with tabs[i]:
                _render_single_ticker_report(analysis, show_header=False)

def _render_single_ticker_report(analysis: StockAnalysis, show_header: bool = True):
    """
    Renders the detailed breakdown for a single ticker.
    """
    if not analysis or not analysis.style_results:
        st.error(f"Missing results for {analysis.ticker if analysis else 'Unknown'}")
        return

    if show_header:
        st.subheader(f"🏁 Multi-Style Strategy Comparison: {analysis.ticker}")
    
    # Hero Recommendation Card
    if analysis.best_style:
        best = analysis.style_results[analysis.best_style]
        with st.container(border=True):
            col_icon, col_text = st.columns([0.15, 0.85])
            with col_icon:
                st.markdown("<h1 style='text-align: center; margin:0;'>🏆</h1>", unsafe_allow_html=True)
            with col_text:
                st.title(f"Best Match for {analysis.ticker}: {analysis.best_style}")
                st.markdown(f"**Confidence Score:** {best['score']:.0%}")
                st.markdown(f"**Thesis:** {best['trend']} setup with {best['rr']:.1f}x Reward/Risk ratio.")
    
    st.divider()
    
    # Comparison Cards
    cols = st.columns(len(analysis.style_results))
    
    for i, (style_name, result) in enumerate(analysis.style_results.items()):
        with cols[i]:
            is_best = (style_name == analysis.best_style)
            
            with st.container(border=True):
                if is_best:
                    st.markdown("⭐ **RECOMMENDED**")
                
                st.markdown(f"### {style_name}")
                st.caption(f"Ticker: {analysis.ticker}")
                
                # Visual Score Bar
                score = result['score']
                score_color = "#4CAF50" if score > 0.7 else "#FFC107" if score > 0.4 else "#F44336"
                st.markdown(f"""
                    <div style="width: 100%; background-color: rgba(128,128,128,0.1); border-radius: 5px; height: 10px; margin-bottom: 5px;">
                        <div style="width: {score*100}%; background-color: {score_color}; height: 10px; border-radius: 5px;"></div>
                    </div>
                """, unsafe_allow_html=True)
                st.caption(f"Setup Quality: {score:.0%}")
                
                st.divider()
                
                # Setup Details
                st.markdown(f"**Trend:** {result['trend']}")
                st.markdown(f"**R/R Ratio:** {result['rr']:.1f}x")
                
                if result['entry']:
                    st.markdown(f"**Entry:** ${result['entry']:.2f}")
                if result['stop']:
                    st.markdown(f"**Stop:** ${result['stop']:.2f}")
                if result['target']:
                    st.markdown(f"**Target:** ${result['target']:.2f}")
                
                # Notes
                with st.expander("Setup Notes"):
                    for note in result['notes']:
                        st.write(note)
                        
                # Patterns
                if result['patterns']:
                    st.caption("🔍 " + ", ".join(result['patterns'][:2]))
                    
                st.divider()
                
                # Deep Dive Button
                button_key = f"btn_dive_{analysis.ticker}_{style_name}"
                if analysis.style_analyses and style_name in analysis.style_analyses:
                    if st.button(f"🔍 View {style_name} Details", key=button_key, use_container_width=True):
                        st.session_state['go_to_page'] = "🏠 Home"
                        st.session_state['active_trading_style'] = style_name
                        st.session_state['current_analysis'] = analysis.style_analyses[style_name]
                        st.session_state['current_ticker'] = analysis.ticker
                        
                        # Apply style defaults
                        from src.trading_styles.factory import get_trading_style
                        style_strategy = get_trading_style(style_name)
                        defaults = style_strategy.get_chart_defaults()
                        if 'chart_prefs' in st.session_state:
                            st.session_state['chart_prefs'].update({
                                'ema': defaults.get('ema', True),
                                'atr': defaults.get('atr', True),
                                'sr': defaults.get('sr', True),
                                'ts': defaults.get('ts', True),
                                'rsi': defaults.get('rsi', False),
                                'macd': defaults.get('macd', False),
                                'boll': defaults.get('boll', False)
                            })
                        st.session_state['timeframe'] = defaults.get('timeframe', 'D')
                        st.session_state['zoom'] = defaults.get('zoom', '1Y')
                        st.rerun()

    # Comparison Grid (Technical Stats)
    st.divider()
    st.subheader(f"📊 Comparative Decision Matrix: {analysis.ticker}")
    
    data = []
    for name, res in analysis.style_results.items():
        data.append({
            "Ticker": analysis.ticker,
            "Style": name,
            "Score": f"{res['score']:.0%}",
            "Trend": res['trend'],
            "R/R": f"{res['rr']:.1f}x",
            "Entry": f"${res['entry']:.2f}" if res['entry'] else "N/A",
            "Target": f"${res['target']:.2f}" if res['target'] else "N/A"
        })
    
    df = pd.DataFrame(data)
    st.table(df)

async def run_multi_style_analysis(ticker: str, analyzer):
    """Bridge to the analyzer's multi_analyze method"""
    return await analyzer.multi_analyze(ticker)
