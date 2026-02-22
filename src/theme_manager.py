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
            /* Override CSS Variables globally */
            :root, .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {{
                --text-color: {colors['text_primary']};
                --background-color: {colors['bg_primary']};
                --secondary-background-color: {colors['bg_secondary']};
                --primary-color: {colors['accent']};
            }}
            
            /* Apply specific background colors */
            .stApp, [data-testid="stAppViewContainer"] {{
                background-color: {colors['bg_primary']} !important;
            }}
            
            [data-testid="stHeader"] {{
                background-color: transparent !important;
            }}
            
            [data-testid="stSidebar"] {{
                background-color: {colors['sidebar_bg']} !important;
            }}
            
            /* Typography overrides for Dark Mode unreadability */
            .stApp, [data-testid="stSidebar"] {{
                color: {colors['text_primary']} !important;
            }}
            
            /* Safely target readable text without breaking dynamic metric colors */
            .stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown li,
            .stText, .stCheckbox label, .stRadio label, .stSelectbox label, .stMultiSelect label, label,
            [data-testid="stMetricLabel"] {{
                color: {colors['text_primary']} !important;
            }}
            
            /* Tabs styling */
            [data-baseweb="tab"] p {{
                color: {colors['text_secondary']} !important;
            }}
            [data-baseweb="tab"][aria-selected="true"] p {{
                color: {colors['accent']} !important;
            }}
            
            /* Dataframes and tables */
            [data-testid="stDataFrame"], .stDataFrame {{
                background-color: {colors['bg_secondary']} !important;
            }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
