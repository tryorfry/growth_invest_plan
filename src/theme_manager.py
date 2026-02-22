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
