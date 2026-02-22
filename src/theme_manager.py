import streamlit as st

class ThemeManager:
    """Manages dynamic Streamlit theme overrides via CSS injection"""
    
    # Define color palettes
    THEMES = {
        'dark': {
            'bg_primary': '#0e1117',
            'bg_secondary': '#262730',
            'text_primary': '#fafafa',
            'text_secondary': '#b0bec5',
            'accent': '#4caf50',
            'border': '#444444',
            'sidebar_bg': '#1e1e1e'
        },
        'light': {
            'bg_primary': '#ffffff',
            'bg_secondary': '#f0f2f6',
            'text_primary': '#31333F',
            'text_secondary': '#555555',
            'accent': '#0068c9',
            'border': '#e6e6e6',
            'sidebar_bg': '#f8f9fa'
        }
    }

    @staticmethod
    def apply_theme():
        """Injects CSS based on the current session's theme preference"""
        # Default to dark if not set (to prevent flashing)
        current_mode = st.session_state.get('theme_preference', 'dark')
        colors = ThemeManager.THEMES.get(current_mode, ThemeManager.THEMES['dark'])
        
        # We target Streamlit's core CSS variables exposed to the root
        css = f"""
        <style>
            :root {{
                --primary-color: {colors['accent']};
                --background-color: {colors['bg_primary']};
                --secondary-background-color: {colors['bg_secondary']};
                --text-color: {colors['text_primary']};
                --font: "Source Sans Pro", sans-serif;
            }}
            
            /* Force exact background colors on standard app containers */
            .stApp {{
                background-color: {colors['bg_primary']} !important;
                color: {colors['text_primary']} !important;
            }}
            
            .css-1d391kg, [data-testid="stSidebar"] {{
                background-color: {colors['sidebar_bg']} !important;
            }}
            
            /* Metric text handling */
            [data-testid="stMetricValue"] {{
                color: {colors['text_primary']} !important;
            }}
            
            /* Tabs styling */
            [data-baseweb="tab"] {{
                color: {colors['text_secondary']} !important;
            }}
            [data-baseweb="tab"][aria-selected="true"] {{
                color: {colors['accent']} !important;
            }}
            
            /* Dataframes and tables */
            .stDataFrame {{
                background-color: {colors['bg_secondary']} !important;
            }}
            
            /* Headers */
            h1, h2, h3, h4, h5, h6 {{
                color: {colors['text_primary']} !important;
            }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
