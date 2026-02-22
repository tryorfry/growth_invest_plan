import streamlit as st
import streamlit.components.v1 as components

st.title("test ls")
components.html("""
<script>
    let keys = Object.keys(window.parent.localStorage);
    console.log(keys);
    document.write("Local Storage Keys in window.parent: " + keys.join(", "));
</script>
""", height=200)
