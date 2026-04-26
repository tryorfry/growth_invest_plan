import streamlit as st
import pandas as pd
import json
import plotly.express as px
from src.database import Database
from src.models import AutomatedReport
import asyncio
import threading

def render_automated_reports_page():
    if st.session_state.get('user_tier') != 'admin':
        st.error("🔒 Admin Only")
        st.stop()
        
    st.title("📊 Automated Trading Reports")
    st.markdown("View interactive data analysis and historical automated trading reports.")
    
    db = st.session_state.get('db')
    if not db:
        db = Database()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        universe = st.radio(
            "Ticker Universe", 
            ["Database Watchlist", "S&P Giants (Top 15 Per Sector)", "🔥 Dynamic Reversal Screener"], 
            horizontal=True,
            captions=[
                "Scans all tickers saved in your portfolio and watchlist.",
                "Scans the top 15 mega-cap companies across 11 sectors.",
                "Scans for mid/large-cap stocks showing high relative volume and a 50-SMA crossing reversal."
            ]
        )
    
    with col2:
        if st.button("🚀 Trigger Run Now", type="primary", use_container_width=True):
            st.info("Report generation started in background. Refresh the page to see progress.")
            import sys
            import os
            import importlib
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
            import scripts.run_daily_reports
            importlib.reload(scripts.run_daily_reports)
            from scripts.run_daily_reports import run_report
            
            tickers = None
            report_type = "Watchlist"
            
            if universe == "S&P Giants (Top 15 Per Sector)":
                from src.data_sources.ticker_scraper import SectorTickerScraper
                tickers = []
                for sector, items in SectorTickerScraper.SP500_GOLDEN_LIST.items():
                    for t, _ in items[:15]:
                        tickers.append(t)
                report_type = "S&P Giants"
            elif universe == "🔥 Dynamic Reversal Screener":
                from src.data_sources.ticker_scraper import DynamicScreener
                screener = DynamicScreener()
                results = screener.fetch_top_candidates(count=30)
                tickers = [r['ticker'] for r in results if r.get('ticker')]
                report_type = "Dynamic Reversal Screener"
                
            def background_task():
                asyncio.run(run_report(tickers=tickers, report_type=report_type))
                
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
                    r_type = getattr(report, 'report_type', 'Standard')
                    st.markdown(f"**[{r_type}]**\n\n{report.report_date.strftime('%Y-%m-%d %H:%M:%S')}")
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
                        if report.error_log:
                            st.caption(f"Error: {report.error_log[:100]}...")
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
                    with st.expander(f"🔍 View Interactive Report ({r_type})", expanded=False):
                        try:
                            data = json.loads(report.report_data_json)
                            df = pd.DataFrame(data)
                            
                            # Inject report type into dataframe for the Data Table tab
                            df.insert(0, "Universe", r_type)
                            
                            # Calculate numeric columns for sorting and plotting
                            if "Checklist Score" in df.columns:
                                df["ScoreNum"] = df["Checklist Score"].apply(lambda x: int(x.split('/')[0]) if isinstance(x, str) and '/' in x else 0)
                            else:
                                df["ScoreNum"] = 0
                                
                            if "R/R" in df.columns:
                                df["RR_Num"] = pd.to_numeric(df["R/R"].astype(str).str.replace('x', ''), errors='coerce').fillna(0)
                            else:
                                df["RR_Num"] = 0
                                
                            # Interactive charts
                            tab1, tab2, tab3, tab4 = st.tabs(["🏆 Top Setups", "Data Table", "Sector Breakdown", "Setup Analysis"])
                            
                            with tab1:
                                try:
                                    if len(df) > 0:
                                        # Sort to find the best 5 stocks
                                        top_stocks = df.sort_values(by=["ScoreNum", "RR_Num"], ascending=[False, False]).head(5)
                                        
                                        st.markdown("### 🔥 Highest Conviction Trade Setups")
                                        st.caption("Ranked by 9-Point Fundamental Quality & Reward-to-Risk Ratio across all trading styles")
                                        
                                        # To handle the first item being expanded
                                        is_first = True
                                        
                                        for idx, top_stock in top_stocks.iterrows():
                                            ticker = top_stock.get('Ticker', 'N/A')
                                            score = top_stock.get('Checklist Score', 'N/A')
                                            best_style = top_stock.get('Best Style', 'N/A')
                                            rr = top_stock.get('R/R', 'N/A')
                                            
                                            # Format R/R cleanly to 2 decimals
                                            if isinstance(rr, (float, int)):
                                                rr_formatted = f"{float(rr):.2f}"
                                            else:
                                                try:
                                                    rr_formatted = f"{float(str(rr).replace('x', '')):.2f}"
                                                except (ValueError, TypeError):
                                                    rr_formatted = str(rr)
                                            
                                            with st.expander(f"⭐ {ticker} - Score: {score} | Style: {best_style} | R/R: {rr_formatted}", expanded=is_first):
                                                is_first = False
                                                st.markdown(f"**Company:** {top_stock.get('Company', 'N/A')} | **Sector:** {top_stock.get('Sector', 'N/A')}")
                                                
                                                col1, col2, col3, col4 = st.columns(4)
                                                col1.metric("Checklist Score", f"{score}")
                                                col2.metric("Best Style", str(best_style))
                                                col3.metric("R/R Ratio", f"{rr_formatted}")
                                                
                                                cp = top_stock.get('Current Price', 'N/A')
                                                col4.metric("Current Price", f"${float(cp):.2f}" if pd.notna(cp) and cp != 'N/A' else "N/A")
                                                
                                                # AI Conviction Summary
                                                ai_summary = top_stock.get("AI Conviction Summary", "N/A")
                                                if ai_summary != "N/A":
                                                    st.markdown("#### 🧠 AI Conviction Summary")
                                                    st.info(ai_summary)

                                                st.markdown("#### Trade Execution Plan")
                                                sc1, sc2, sc3, sc4 = st.columns(4)
                                                
                                                def fmt_val(v):
                                                    if v == 'N/A' or v is None: return 'N/A'
                                                    try:
                                                        f = float(v)
                                                        return f"{int(f)}" if f % 1 == 0 else f"{f:.2f}"
                                                    except: return str(v)

                                                with sc1:
                                                    st.info(f"**Suggested Entry:**\n\n{fmt_val(top_stock.get('Suggested Entry'))}")
                                                with sc2:
                                                    st.error(f"**Stop Loss:**\n\n{fmt_val(top_stock.get('Stop Loss'))}")
                                                with sc3:
                                                    st.success(f"**Target Price:**\n\n{fmt_val(top_stock.get('Target Price'))}")
                                                with sc4:
                                                    st.warning(f"**Position Size (Units):**\n\n{fmt_val(top_stock.get('Position Size (Units)'))}")
                                                    
                                                st.markdown("#### Volatility & Risk Metrics")
                                                vr1, vr2, vr3, vr4 = st.columns(4)
                                                atr = top_stock.get('ATR', 'N/A')
                                                atr_w = top_stock.get('Weekly ATR', 'N/A')
                                                
                                                atr_str = f"{float(atr):.2f}" if isinstance(atr, (int, float)) and pd.notna(atr) else str(atr)
                                                atrw_str = f"{float(atr_w):.2f}" if isinstance(atr_w, (int, float)) and pd.notna(atr_w) else str(atr_w)
                                                
                                                vr1.metric("Daily ATR (14d)", atr_str)
                                                vr2.metric("Weekly ATR (14w)", atrw_str)
                                                vr3.metric("Next Earnings", f"{top_stock.get('Next Earnings', 'N/A')}")
                                                
                                                ed = top_stock.get('Expected Earnings Deviation', 'N/A')
                                                ed_str = f"{float(ed):.2f}%" if isinstance(ed, (int, float)) and pd.notna(ed) else str(ed)
                                                vr3.metric("Expected E-Deviation", ed_str)

                                                st.markdown("#### Institutional Flow & Analyst Tracking")
                                                f1, f2, f3, f4 = st.columns(4)
                                                f1.metric("Inst Own", top_stock.get('Inst Own', 'N/A'))
                                                f2.metric("Inst Trans", top_stock.get('Inst Trans', 'N/A'))
                                                f3.metric("Insider Own", top_stock.get('Insider Own', 'N/A'))
                                                f4.metric("Insider Trans", top_stock.get('Insider Trans', 'N/A'))
                                                
                                                st.caption(f"**Recent Analyst Action:** {top_stock.get('Recent Action', 'N/A')}")

                                                st.markdown("#### Multi-Style Algorithm Strength")
                                                ss1, ss2, ss3 = st.columns(3)
                                                
                                                def fmt_score(s):
                                                    try: return f"{int(float(s)*100)}/100"
                                                    except: return f"{s}/100"
                                                    
                                                ss1.metric("Growth Score", fmt_score(top_stock.get('Growth Score', 0)))
                                                ss2.metric("Swing Score", fmt_score(top_stock.get('Swing Score', 0)))
                                                ss3.metric("Trend Score", fmt_score(top_stock.get('Trend Score', 0)))
                                                
                                                # Show the breakdown of the 9-point checklist
                                                details = top_stock.get('Checklist Details')
                                                if isinstance(details, dict):
                                                    st.markdown("#### 9-Point Checklist Breakdown")
                                                    for key, info in details.items():
                                                        icon = "✅" if info.get('pass') else "❌"
                                                        st.markdown(f"{icon} **{key}**: {info.get('label')}")
                                                
                                                st.divider()
                                                # New Tab / Deep Dive Router
                                                # Streamlit natively supports st.page_link, but since we use radio buttons for routing,
                                                # we inject an HTML link that uses query parameters. We'll update dashboard.py to handle it!
                                                st.markdown(f'<a href="/?ticker={ticker}" target="_blank" style="text-decoration:none;"><button style="width:100%; padding:0.5rem; background-color:#1E88E5; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold;">🔬 Open Deep Dive Analysis in New Tab</button></a>', unsafe_allow_html=True)
                                    else:
                                        st.info("No data available to determine top performers.")
                                except Exception as e:
                                    st.error(f"Could not calculate top performers: {e}")
                            
                            with tab2:
                                st.dataframe(df, use_container_width=True)
                                
                            with tab3:
                                if "Sector" in df.columns:
                                    sector_counts = df["Sector"].value_counts().reset_index()
                                    sector_counts.columns = ["Sector", "Count"]
                                    fig = px.pie(sector_counts, values="Count", names="Sector", title="Analyzed Stocks by Sector", hole=0.4)
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.info("Sector data missing.")
                                    
                            with tab4:
                                st.markdown("### Risk vs Reward Landscape")
                                st.caption("Bubble size represents Checklist Score. The top-right corner indicates the most ideal setups (High Quality, High R/R).")
                                
                                plot_df = df.copy()
                                # Cap extreme R/R ratios so the chart remains readable
                                plot_df["RR_Cap"] = plot_df["RR_Num"].clip(upper=10) 
                                
                                fig3 = px.scatter(
                                    plot_df, 
                                    x="ScoreNum", 
                                    y="RR_Cap", 
                                    color="Sector" if "Sector" in plot_df.columns else None,
                                    hover_name="Ticker",
                                    hover_data=["Company", "R/R", "Checklist Score", "Best Style"],
                                    size="ScoreNum",
                                    size_max=20,
                                    title="Fundamental Quality vs Reward-to-Risk",
                                    labels={"ScoreNum": "9-Point Checklist Score", "RR_Cap": "Reward/Risk Ratio (Capped at 10x)"}
                                )
                                fig3.update_xaxes(type='category', categoryorder='array', categoryarray=list(range(10)))
                                st.plotly_chart(fig3, use_container_width=True)
                                    
                        except Exception as e:
                            st.error(f"Error rendering interactive report: {e}")
                            
                elif report.status == 'failed':
                    with st.expander("View Error"):
                        st.error(report.error_log)
