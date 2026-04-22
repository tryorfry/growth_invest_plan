import plotly.graph_objects as go
import streamlit as st
import pandas as pd
from typing import List, Dict, Any

@st.cache_data(ttl=600, show_spinner=False)
def create_market_map_fig(snapshot_data: List[Dict[str, Any]], is_dark: bool):
    """
    Creates an interactive World Map figure showing global market performance Pulse.
    Cached for 10 minutes to avoid redundant heavy Plotly figure generation.
    """
    # Filter for items with coordinate data
    geo_data = [d for d in snapshot_data if d.get('lat') is not None]
    
    if not geo_data:
        return None

    df = pd.DataFrame(geo_data)
    
    # Scale bubble size by the absolute magnitude of change
    df['bubble_size'] = df['pct_change'].abs().clip(0.1, 5) * 5 + 10
    
    # Determine color based on performance
    df['color'] = df['pct_change'].apply(lambda x: '#10b981' if x >= 0 else '#ef4444')
    
    # Text labels (Permanent beside bubbles)
    df['label_text'] = df.apply(lambda r: f"{r['short']}: {r['pct_change']:+.1f}%", axis=1)
    
    # Create the figure
    fig = go.Figure()

    # 1. Add the "Pulse" bubbles (Markers only)
    fig.add_trace(go.Scattergeo(
        lat=df['lat'],
        lon=df['lon'],
        mode='markers+text',
        marker=dict(
            size=df['bubble_size'],
            color=df['color'],
            opacity=0.7,
            symbol='circle',
            line=dict(width=1, color='white')
        ),
        text=df['label_text'],
        textposition="top center",
        textfont=dict(size=10),
        hovertext=df.apply(lambda r: f"<b>{r['name']}</b><br>Value: {r['value']:,.2f}<br>Change: {r['pct_change']:+.2f}%", axis=1),
        hoverinfo='text'
    ))

    # Determine map colors
    land_color = 'rgb(30, 41, 59)' if is_dark else 'rgb(241, 245, 249)'
    ocean_color = 'rgb(15, 23, 42)' if is_dark else 'rgb(226, 232, 240)'
    
    # Apply dynamic colors to text
    fig.update_traces(textfont_color='white' if is_dark else 'black')

    fig.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='natural earth',
            landcolor=land_color,
            oceancolor=ocean_color,
            showocean=True,
            showlakes=False,
            showcountries=True,
            countrycolor='rgba(255, 255, 255, 0.1)' if is_dark else 'rgba(0, 0, 0, 0.1)',
            bgcolor='rgba(0,0,0,0)'
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=450,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def render_global_market_map(snapshot_data: List[Dict[str, Any]]):
    """
    Renders the cached global market map.
    """
    is_dark = st.session_state.get('theme_preference', 'dark') == 'dark'
    
    # Cache the figure itself to avoid CPU spikes on script reruns
    fig = create_market_map_fig(snapshot_data, is_dark)
    
    if fig:
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
