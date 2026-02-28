import streamlit as st

class ThemeManager:
    """Manages Streamlit theme by aggressively enforcing native global config"""

    @staticmethod
    def apply_theme():
        """Synchronizes the server global theme configuration with the active user's session preference"""
        # Get the desired theme from session state, defaulting to dark
        desired_theme = st.session_state.get('theme_preference', 'dark')
        
        # Get the currently set global theme
        try:
            current_theme = st._config.get_option('theme.base')
        except Exception:
            current_theme = None
            
        # If the server's global CSS renderer isn't currently outputting the user's desired theme,
        # Force a programmatic override via CSS mapping since Streamlit Cloud often caches the `.toml`
        if desired_theme == 'light':
            st.markdown("""
                <style>
                    :root {
                        --primary-color: #f0f2f6;
                        --background-color: #ffffff;
                        --secondary-background-color: #f0f2f6;
                        --text-color: #31333F;
                        --font: "Inter", sans-serif;
                    }
                    /* Force Streamlit app background and text */
                    .stApp {
                        background-color: var(--background-color) !important;
                        color: var(--text-color) !important;
                    }
                    
                    /* Force text elements */
                    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {
                        color: var(--text-color) !important;
                    }
                    
                    /* Force secondary backgrounds like sidebars and containers */
                    section[data-testid="stSidebar"],
                    div[data-testid="stExpander"],
                    div.stForm,
                    div[data-testid="stMetric"] {
                        background-color: var(--secondary-background-color) !important;
                        border-color: #d0d2d6 !important;
                    }
                    
                    /* Input elements */
                    .stTextInput input, .stSelectbox select, .stSlider > div {
                        background-color: #ffffff !important;
                        color: #31333F !important;
                        border-color: #d0d2d6 !important;
                    }
                </style>
            """, unsafe_allow_html=True)

    @staticmethod
    def inject_custom_css():
        """Injects global CSS for mobile responsiveness, typography, and premium polish."""
        st.markdown(
            """
            <style>
            /* Import Premium Fonts */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            
            /* Global Typography */
            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif;
            }
            
            /* Mobile Responsiveness & Polish */
            @media (max-width: 768px) {
                /* Reduce aggressive padding on mobile */
                .block-container {
                    padding-top: 2rem !important;
                    padding-left: 1rem !important;
                    padding-right: 1rem !important;
                }
                
                /* Ensure columns stack gracefully instead of squishing */
                [data-testid="column"] {
                    width: 100% !important;
                    flex: 1 1 100% !important;
                    min-width: 100% !important;
                    margin-bottom: 1rem !important;
                }
                
                /* Make DataFrames scroll horizontally on small screens */
                [data-testid="stDataFrame"] > div {
                    overflow-x: auto;
                }
                
                /* Tweak metric text sizes for mobile context */
                [data-testid="stMetricValue"] {
                    font-size: 1.8rem !important;
                }
            }
            
            /* Add subtle hover effects to buttons */
            button[kind="primary"] {
                transition: transform 0.1s ease-in-out, box-shadow 0.1s ease-in-out;
            }
            button[kind="primary"]:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            </style>
            """,
            unsafe_allow_html=True
        )
