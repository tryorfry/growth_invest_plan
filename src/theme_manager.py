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
        # force it to switch and trigger a proactive reload so the React frontend adopts it natively.
        if current_theme != desired_theme:
            st._config.set_option('theme.base', desired_theme)
            
            # Explicitly force the primary contrast colors mapping Streamlit's native theme pallets
            if desired_theme == 'dark':
                st._config.set_option('theme.backgroundColor', '#0e1117')
                st._config.set_option('theme.secondaryBackgroundColor', '#262730')
                st._config.set_option('theme.textColor', '#fafafa')
            else:
                st._config.set_option('theme.backgroundColor', '#ffffff')
                st._config.set_option('theme.secondaryBackgroundColor', '#f0f2f6')
                st._config.set_option('theme.textColor', '#31333F')
                
            st.rerun()

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
