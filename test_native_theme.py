import streamlit as st

if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

# Set theme config BEFORE anything else
st._config.set_option('theme.base', st.session_state.theme)
st._config.set_option('theme.primaryColor', '#4caf50')

st.title("Native Theme Test")
st.sidebar.markdown("This is sidebar text")

if st.button("Toggle to " + ('Light' if st.session_state.theme == 'dark' else 'Dark')):
    st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
    st._config.set_option('theme.base', st.session_state.theme)
    st.rerun()

st.write(f"Active Theme in State: {st.session_state.theme}")
st.selectbox("Test Select", ["A", "B"])
