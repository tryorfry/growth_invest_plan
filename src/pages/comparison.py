"""Comparison and visualization page for Streamlit dashboard"""

import streamlit as st
import asyncio
from src.analyzer import StockAnalyzer
from src.visualization_advanced import AdvancedVisualizations


def render_comparison_page():
    """Render the stock comparison page"""
    st.title("📈 Stock Comparison")
    
    # Ticker input
    st.subheader("Select Stocks to Compare")
    
    # Sidebar integration for history
    db = st.session_state.get('db')
    db_tickers = []
    if db:
        db_tickers = db.get_all_tickers()
        
    with st.sidebar:
        st.divider()
        st.subheader("Search History")
        if db_tickers:
            st.info("💡 Use the dropdowns below or select from history to compare.")
            hist_selection = st.selectbox("Quick Select from History", options=["-- Select --"] + db_tickers, key="comp_hist")
        else:
            st.info("No analysis history found.")

    col1, col2, col3 = st.columns(3)
    with col1:
        val1 = hist_selection if hist_selection != "-- Select --" else "AAPL"
        ticker1 = st.text_input("Ticker 1", value=val1).upper()
    with col2:
        ticker2 = st.text_input("Ticker 2", value="NVDA").upper()
    with col3:
        ticker3 = st.text_input("Ticker 3 (optional)").upper()
    
    normalize = st.checkbox("Normalize Prices (Base = 100)", value=True)
    
    if st.button("Compare", type="primary"):
        tickers = [t for t in [ticker1, ticker2, ticker3] if t]
        
        if len(tickers) < 2:
            st.error("Please enter at least 2 tickers to compare")
            return
        
        with st.spinner("Analyzing stocks..."):
            analyzer = StockAnalyzer()
            viz = AdvancedVisualizations()
            analyses = []
            
            # Analyze all tickers
            for ticker in tickers:
                try:
                    analysis = asyncio.run(analyzer.analyze(ticker))
                    if analysis:
                        analyses.append(analysis)
                except Exception as e:
                    st.error(f"Error analyzing {ticker}: {e}")
            
            if len(analyses) < 2:
                st.error("Need at least 2 successful analyses to compare")
                return
            
            # Display Quick Info for each stock
            st.subheader("Stock Info & Links")
            info_cols = st.columns(len(analyses))
            for i, analysis in enumerate(analyses):
                with info_cols[i]:
                    st.markdown(f"**{analysis.ticker}**")
                    analysis_time = analysis.analysis_timestamp.strftime('%Y-%m-%d %H:%M') if analysis.analysis_timestamp else "N/A"
                    st.caption(f"🕒 Analyzed: {analysis_time}")
                    yfin_url = f"https://finance.yahoo.com/quote/{analysis.ticker}"
                    finviz_url = f"https://finviz.com/quote.ashx?t={analysis.ticker}"
                    st.markdown(f"[YFinance]({yfin_url}) | [Finviz]({finviz_url})")
            
            st.divider()
            
            # Display comparison chart
            st.subheader("Price Comparison")
            fig = viz.create_comparison_chart(analyses, normalize=normalize)
            if fig:
                st.plotly_chart(fig, width='stretch')
            
            # Performance table
            st.subheader("Performance Metrics")
            perf_df = viz.create_performance_table(analyses)
            if not perf_df.empty:
                st.dataframe(perf_df, width='stretch')
            
            # Correlation heatmap
            if len(analyses) >= 2:
                st.subheader("Correlation Matrix")
                corr_fig = viz.create_correlation_heatmap(analyses)
                if corr_fig:
                    st.plotly_chart(corr_fig, width='stretch')
                    
                    st.info("""
                    **Correlation Interpretation:**
                    - 1.0 = Perfect positive correlation (stocks move together)
                    - 0.0 = No correlation
                    - -1.0 = Perfect negative correlation (stocks move opposite)
                    """)
            
            # Sector heatmap
            if len(analyses) >= 3:
                st.subheader("Sector Performance")
                sector_fig = viz.create_sector_heatmap(analyses)
                if sector_fig:
                    st.plotly_chart(sector_fig, width='stretch')


if __name__ == "__main__":
    render_comparison_page()
