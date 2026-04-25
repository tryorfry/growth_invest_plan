import streamlit as st
import pandas as pd
import json
import plotly.express as px
from src.database import Database
from src.models import AutomatedReport
import asyncio
import threading

def render_automated_reports_page():
    st.title("📊 Automated Trading Reports")
    st.markdown("View interactive data analysis and historical automated trading reports.")
    
    db = st.session_state.get('db')
    if not db:
        db = Database()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        universe = st.radio("Ticker Universe", ["Database Watchlist", "S&P Giants (Top 15 Per Sector)"], horizontal=True)
    
    with col2:
        if st.button("🚀 Trigger Run Now", type="primary", use_container_width=True):
            st.info("Report generation started in background. Refresh the page to see progress.")
            import sys
            import os
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
            from scripts.run_daily_reports import run_report
            
            tickers = None
            if universe == "S&P Giants (Top 15 Per Sector)":
                from src.data_sources.ticker_scraper import SectorTickerScraper
                tickers = []
                for sector, items in SectorTickerScraper.SP500_GOLDEN_LIST.items():
                    for t, _ in items[:15]:
                        tickers.append(t)
                
            def background_task():
                asyncio.run(run_report(tickers=tickers))
                
            thread = threading.Thread(target=background_task)
            thread.start()
            st.rerun()
            
    st.divider()
    
    with db.get_session() as session:
        reports = session.query(AutomatedReport).order_by(AutomatedReport.report_date.desc()).limit(50).all()
        
        if not reports:
            st.info("No historical reports found.")
            return
            
        # Check if any report is running to show a refresh button at the top
        is_running = any(r.status == 'running' for r in reports)
        if is_running:
            if st.button("🔄 Refresh Progress", use_container_width=True):
                st.rerun()
            
        for report in reports:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 1, 2, 1])
                
                with c1:
                    st.markdown(f"**Date:** {report.report_date.strftime('%Y-%m-%d %H:%M:%S')}")
                with c2:
                    st.markdown(f"**Stocks:** {report.total_stocks_analyzed}")
                with c3:
                    if report.status == 'completed':
                        st.markdown(f"**Status:** :green[{report.status}]")
                    elif report.status == 'running':
                        pct = report.progress_pct if report.progress_pct is not None else 0
                        st.markdown(f"**Status:** :blue[{report.status}] - {pct}%")
                        st.progress(pct / 100.0)
                        if report.current_ticker:
                            st.caption(f"Processing: {report.current_ticker}")
                    else:
                        st.markdown(f"**Status:** :red[{report.status}]")
                with c4:
                    if report.status == 'completed' and report.report_data_json:
                        try:
                            # Direct parsing inside the download button
                            st.download_button(
                                label="⬇️ CSV",
                                data=pd.DataFrame(json.loads(report.report_data_json)).to_csv(index=False).encode('utf-8'),
                                file_name=f"report_{report.report_date.strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                key=f"dl_btn_{report.id}"
                            )
                        except Exception as e:
                            st.error(f"Data error")
                
                if report.status == 'completed' and report.report_data_json:
                    with st.expander("🔍 View Interactive Report", expanded=False):
                        try:
                            data = json.loads(report.report_data_json)
                            df = pd.DataFrame(data)
                            
                            # Interactive charts
                            tab1, tab2, tab3 = st.tabs(["Data Table", "Sector Breakdown", "Checklist Scores"])
                            
                            with tab1:
                                st.dataframe(df, use_container_width=True)
                                
                            with tab2:
                                if "Sector" in df.columns:
                                    sector_counts = df["Sector"].value_counts().reset_index()
                                    sector_counts.columns = ["Sector", "Count"]
                                    fig = px.pie(sector_counts, values="Count", names="Sector", title="Analyzed Stocks by Sector", hole=0.4)
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.info("Sector data missing.")
                                    
                            with tab3:
                                if "Checklist Score" in df.columns:
                                    # Extract just the numerator (e.g. "8/9" -> 8)
                                    df["ScoreNum"] = df["Checklist Score"].apply(lambda x: int(x.split('/')[0]) if isinstance(x, str) and '/' in x else 0)
                                    score_counts = df["ScoreNum"].value_counts().reset_index()
                                    score_counts.columns = ["Score", "Count"]
                                    score_counts = score_counts.sort_values("Score")
                                    fig2 = px.bar(score_counts, x="Score", y="Count", title="Fundamental Checklist Score Distribution")
                                    fig2.update_xaxes(type='category')
                                    st.plotly_chart(fig2, use_container_width=True)
                                else:
                                    st.info("Score data missing.")
                                    
                        except Exception as e:
                            st.error(f"Error rendering interactive report: {e}")
                            
                elif report.status == 'failed':
                    with st.expander("View Error"):
                        st.error(report.error_log)
