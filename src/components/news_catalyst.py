import streamlit as st
from typing import List, Dict, Any

def render_news_catalysts(news_data: Dict[str, Any]):
    """
    Renders Top 3 news headlines as high-fidelity cards with sentiment badges.
    """
    with st.expander("🗞️ Latest Catalysts & News", expanded=False):
        articles = news_data.get('articles', [])
        if not articles:
            st.info("No recent high-impact news catalysts found for this ticker.")
            return
        
        # Limit to Top 3 for brokerage-style clarity
        for article in articles[:3]:
            # Safety: Ensure link is a string, not a dict (prevents markdown junk)
            link = article.get('link', '#')
            if isinstance(link, dict):
                link = link.get('url', '#')
                
            with st.container(border=True):
                col1, col2 = st.columns([0.8, 0.2])
                
                with col1:
                    st.markdown(f"**[{article['title']}]({link})**")
                    st.caption(f"Source: {article['publisher']} | Date: {article['date']}")
                    
                with col2:
                    # Map sentiment labels to colors
                    label = article.get('sentiment_label', 'Neutral')
                    if label == 'Bullish':
                        color = "#10b981" # Emerald Green
                        icon = "📈"
                    elif label == 'Bearish':
                        color = "#ef4444" # Red
                        icon = "📉"
                    else:
                        color = "#94a3b8" # Slate Gray
                        icon = "⚖️"
                    
                    st.markdown(f"""
                        <div style="background-color: {color}22; border: 1px solid {color}; 
                                    color: {color}; border-radius: 8px; padding: 4px 8px; 
                                    text-align: center; font-size: 0.8rem; font-weight: 700;">
                            {icon} {label}
                        </div>
                    """, unsafe_allow_html=True)

    st.write("")
