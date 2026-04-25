import streamlit as st
import pandas as pd
import json
from src.database import Database
from src.models import AutomatedReport
import asyncio

def render_automated_reports_page():
    st.title("📊 Automated Trading Reports")
    st.markdown("View and download historical automated trading reports.")
    
    db = st.session_state.get('db')
    if not db:
        db = Database()
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🚀 Trigger Run Now", type="primary", use_container_width=True):
            with st.spinner("Generating reports... this might take a few minutes."):
                import sys
                import os
                # Ensure the root is in path so scripts module can be imported
                sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
                
                from scripts.run_daily_reports import run_report
                try:
                    # Run the report generator
                    asyncio.run(run_report())
                    st.success("Report generation complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to generate report: {e}")
    
    st.divider()
    
    with db.get_session() as session:
        reports = session.query(AutomatedReport).order_by(AutomatedReport.report_date.desc()).limit(50).all()
        
        if not reports:
            st.info("No historical reports found.")
            return
            
        for report in reports:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                
                with c1:
                    st.markdown(f"**Date:** {report.report_date.strftime('%Y-%m-%d %H:%M:%S')}")
                with c2:
                    st.markdown(f"**Stocks:** {report.total_stocks_analyzed}")
                with c3:
                    if report.status == 'completed':
                        st.markdown(f"**Status:** :green[{report.status}]")
                    elif report.status == 'running':
                        st.markdown(f"**Status:** :blue[{report.status}]")
                    else:
                        st.markdown(f"**Status:** :red[{report.status}]")
                with c4:
                    if report.status == 'completed' and report.report_data_json:
                        try:
                            # Parse JSON to DataFrame for CSV export
                            data = json.loads(report.report_data_json)
                            df = pd.DataFrame(data)
                            csv = df.to_csv(index=False).encode('utf-8')
                            
                            st.download_button(
                                label="⬇️ Download CSV",
                                data=csv,
                                file_name=f"report_{report.report_date.strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                key=f"dl_btn_{report.id}"
                            )
                        except Exception as e:
                            st.error(f"Data error")
                    elif report.status == 'failed':
                        with st.expander("View Error"):
                            st.error(report.error_log)
