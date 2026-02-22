import streamlit as st

if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

st.title("Theme Test")

if st.button("Toggle Theme"):
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
    
st._config.set_option('theme.base', st.session_state.theme)
st.write(f"Current theme set to: {st.session_state.theme}")
