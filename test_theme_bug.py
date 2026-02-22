import streamlit as st
import time

if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

st.title("Theme UI Test")
st.sidebar.markdown("This is sidebar text")

if st.button("Toggle Light/Dark"):
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
    st._config.set_option('theme.base', st.session_state.theme)
    st.rerun()

st.write(f"Active Theme in State: {st.session_state.theme}")
