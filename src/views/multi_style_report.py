import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
from typing import Dict, Any, Optional, List, Union
from src.analyzer import StockAnalysis
from src.utils_correlation import calculate_correlation_matrix
from src.exporters.excel_exporter import ExcelExporter
from src.watchlist import WatchlistManager

from src.alerts.alert_engine import AlertEngine

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

    # 1. Action Bar (Excel Export & Alerts)
    if len(analyses) > 1:
        col_export, col_alert, col_empty = st.columns([0.3, 0.3, 0.4])
        with col_export:
            if st.button("📥 Download Batch Excel Report", use_container_width=True):
                exporter = ExcelExporter()
                filename = exporter.export_analysis(analyses)
                with open(filename, "rb") as f:
                    st.download_button(
                        label="Click here to save file",
                        data=f,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        with col_alert:
            if st.button("🔔 Sync Best Match Alerts", use_container_width=True):
                from src.database import Database
                db = Database()
                ae = AlertEngine()
                count = 0
                with db.get_session() as session:
                    for a in analyses:
                        if a.best_style:
                            best = a.style_results[a.best_style]
                            if best['entry']:
                                # Create alert for price crosses below entry
                                ae.create_alert(
                                    session, 
                                    a.ticker, 
                                    'price', 
                                    'below', 
                                    best['entry'], 
                                    st.session_state.get('user_id', 1)
                                )
                                count += 1
                if count > 0:
                    st.success(f"Successfully synced {count} price alerts based on entry setups!")
                else:
                    st.info("No valid entries found to create alerts.")

        st.divider()

    # 2. Summary Leaderboard with Watchlist Integration
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
                    "ScoreNum": best['score'],
                    "Sector": analysis.sector or "Unknown"
                })
        
        if leaderboard_data:
            df_leader = pd.DataFrame(leaderboard_data)
            df_leader = df_leader.sort_values('ScoreNum', ascending=False)
            
            # Watchlist multi-select
            selected_tickers = st.multiselect(
                "Select tickers to add to Watchlist",
                options=df_leader['Ticker'].tolist(),
                default=[]
            )
            
            if selected_tickers and st.button("➕ Add Selected to Watchlist"):
                from src.database import Database
                db = Database()
                with db.get_session() as session:
                    # session, user_id
                    wm = WatchlistManager(session, st.session_state.get('user_id', 1))
                    watchlist = wm.get_default_watchlist()
                    for t in selected_tickers:
                        # Find the analysis object for notes
                        an = next((a for a in analyses if a.ticker == t), None)
                        note = f"Added from Multi-Style Analysis. Best style: {an.best_style}" if an else ""
                        wm.add_stock_to_watchlist(watchlist.id, t, note)
                    st.success(f"Added {len(selected_tickers)} stocks to '{watchlist.name}'")

            st.dataframe(df_leader.drop(columns=['ScoreNum']), use_container_width=True, hide_index=True)
            
        st.divider()

    # 3. Sector Intelligence & Benchmarking
    if len(analyses) > 1:
        st.subheader("🏢 Sector Intelligence & Benchmarking")
        sector_data = []
        for analysis in analyses:
            if analysis.best_style:
                sector_data.append({
                    "Sector": analysis.sector or "Unknown",
                    "Ticker": analysis.ticker,
                    "Score": analysis.style_results[analysis.best_style]['score'],
                    "R/R": analysis.style_results[analysis.best_style]['rr']
                })
        
        if sector_data:
            df_sector = pd.DataFrame(sector_data)
            sector_bench = df_sector.groupby('Sector').agg({
                'Ticker': 'count',
                'Score': 'mean',
                'R/R': 'mean'
            }).rename(columns={'Ticker': 'Stock Count', 'Score': 'Avg Setup Quality', 'R/R': 'Avg R/R'})
            
            sector_bench['Avg Setup Quality'] = sector_bench['Avg Setup Quality'].apply(lambda x: f"{x:.0%}")
            sector_bench['Avg R/R'] = sector_bench['Avg R/R'].apply(lambda x: f"{x:.2f}x")
            
            st.table(sector_bench)
            
            with st.expander("🔍 View Top Outperformers by Sector"):
                for sector, group in df_sector.groupby('Sector'):
                    top_idx = group['Score'].idxmax()
                    top_stock = group.loc[top_idx]
                    st.markdown(f"**{sector}:** {top_stock['Ticker']} is the leader with {top_stock['Score']:.0%} setup.")
        st.divider()

    # 4. Correlation Discovery (Risk Heatmap)
    if len(analyses) > 1:
        st.subheader("🔗 Correlation Discovery (Risk Heatmap)")
        with st.spinner("Calculating price correlations..."):
            corr_matrix = calculate_correlation_matrix(analyses)
            if not corr_matrix.empty:
                fig = px.imshow(
                    corr_matrix,
                    text_auto=".2f",
                    aspect="auto",
                    color_continuous_scale="RdBu_r",
                    origin="lower",
                    labels=dict(color="Correlation")
                )
                fig.update_layout(title="Daily Returns Correlation")
                st.plotly_chart(fig, use_container_width=True)
                
                # Risk Analysis
                if len(corr_matrix) > 1:
                    avg_corr = (corr_matrix.sum().sum() - len(corr_matrix)) / (len(corr_matrix)**2 - len(corr_matrix))
                    if avg_corr > 0.7:
                        st.warning(f"⚠️ **High Concentration Risk:** Average correlation is {avg_corr:.2f}. These stocks move very closely together.")
                    elif avg_corr < 0.3:
                        st.success(f"✅ **Good Diversification:** Average correlation is {avg_corr:.2f}. These stocks provide low-correlated exposure.")
                    else:
                        st.info(f"ℹ️ **Moderate Correlation:** Average correlation is {avg_corr:.2f}.")
            else:
                st.info("Insufficient historical data to calculate correlations.")
        st.divider()

    # 5. Cross-Style Comparison Matrix (All Tickers x All Styles)
    if len(analyses) > 1:
        st.subheader("📊 Cross-Style Comparison Matrix")
        matrix_data = []
        for analysis in analyses:
            for style_name, res in analysis.style_results.items():
                matrix_data.append({
                    "Ticker": analysis.ticker,
                    "Style": style_name,
                    "Score": f"{res['score']:.0%}",
                    "Trend": res['trend'],
                    "R/R": f"{res['rr']:.1f}x",
                    "Target Upside": f"{((res['target']-analysis.current_price)/analysis.current_price)*100:+.1f}%" if res['target'] and analysis.current_price else "N/A"
                })
        
        df_matrix = pd.DataFrame(matrix_data)
        st.dataframe(df_matrix, use_container_width=True, hide_index=True)
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
                
                if result['entry'] and result['stop']:
                    try:
                        risk_pu = float(result['entry']) - float(result['stop'])
                        if risk_pu > 0:
                            units = 100.0 / risk_pu
                            units_fmt = f"{units:.2f}" if not units.is_integer() else f"{int(units)}"
                            st.caption(f"⚖️ **Risk/Unit:** ${risk_pu:.2f} | **Max Units (1%):** {units_fmt}")
                    except ValueError:
                        pass
                
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
                style_analyses = getattr(analysis, 'style_analyses', {})
                if style_analyses and style_name in style_analyses:
                    if st.button(f"🔍 View {style_name} Details", key=button_key, use_container_width=True):
                        st.session_state['go_to_page'] = "🏠 Home"
                        st.session_state['active_trading_style'] = style_name
                        st.session_state['current_analysis'] = analysis.style_analyses[style_name]
                        st.session_state['current_ticker'] = analysis.ticker
                        
                        # Force Home page ticker to match
                        st.session_state['main_dash_text'] = analysis.ticker
                        st.session_state['main_dash_dropdown'] = ""

                        
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
        risk_pu_str = "N/A"
        units_str = "N/A"
        if res.get('entry') and res.get('stop'):
            try:
                rpu = float(res['entry']) - float(res['stop'])
                if rpu > 0:
                    risk_pu_str = f"${rpu:.2f}"
                    units = 100.0 / rpu
                    units_str = f"{units:.2f}" if not units.is_integer() else f"{int(units)}"
            except ValueError:
                pass

        data.append({
            "Ticker": analysis.ticker,
            "Style": name,
            "Score": f"{res['score']:.0%}",
            "Trend": res['trend'],
            "R/R": f"{res['rr']:.1f}x",
            "Entry": f"${res['entry']:.2f}" if res['entry'] else "N/A",
            "Target": f"${res['target']:.2f}" if res['target'] else "N/A",
            "Risk/Unit": risk_pu_str,
            "Max Units": units_str
        })
    
    df = pd.DataFrame(data)
    st.table(df)

async def run_multi_style_analysis(ticker: str, analyzer):
    """Bridge to the analyzer's multi_analyze method"""
    return await analyzer.multi_analyze(ticker)
