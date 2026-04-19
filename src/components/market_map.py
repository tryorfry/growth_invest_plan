import plotly.graph_objects as go
import streamlit as st
import pandas as pd
from typing import List, Dict, Any

def render_global_market_map(snapshot_data: List[Dict[str, Any]]):
    """
    Renders an interactive World Map showing global market performance Pulse.
    """
    # Filter for items with coordinate data (indices only, no crypto)
    geo_data = [d for d in snapshot_data if d.get('lat') is not None]
    
    if not geo_data:
        return

    df = pd.DataFrame(geo_data)
    
    # Scale bubble size by the absolute magnitude of change
    # Min size 10, max size 30
    df['bubble_size'] = df['pct_change'].abs().clip(0.1, 5) * 5 + 10
    
    # Determine color based on performance
    df['color'] = df['pct_change'].apply(lambda x: '#10b981' if x >= 0 else '#ef4444')
    
    # Create the figure
    fig = go.Figure(go.Scattergeo(
        lat=df['lat'],
        lon=df['lon'],
        mode='markers',
        marker=dict(
            size=df['bubble_size'],
            color=df['color'],
            opacity=0.7,
            symbol='circle',
            line=dict(width=1, color='rgba(255, 255, 255, 0.5)')
        ),
        text=df.apply(lambda r: f"<b>{r['name']}</b><br>{r['country']}<br>Change: {r['pct_change']:+.2f}%", axis=1),
        hoverinfo='text'
    ))

    # Determine map theme based on app theme
    is_dark = st.session_state.get('theme_preference', 'dark') == 'dark'
    land_color = 'rgb(30, 41, 59)' if is_dark else 'rgb(241, 245, 249)'
    ocean_color = 'rgb(15, 23, 42)' if is_dark else 'rgb(226, 232, 240)'
    lake_color = ocean_color
    
    fig.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='natural earth',
            landcolor=land_color,
            oceancolor=ocean_color,
            lakecolor=lake_color,
            showocean=True,
            showlakes=True,
            showcountries=True,
            countrycolor='rgba(255, 255, 255, 0.1)' if is_dark else 'rgba(0, 0, 0, 0.1)',
            bgcolor='rgba(0,0,0,0)' # Transparent background
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
