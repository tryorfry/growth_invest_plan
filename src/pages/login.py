"""Login and Registration Page"""

import streamlit as st
from src.auth import AuthManager

def render_login_page():
    st.title("🔐 Authentication")
    st.markdown("Please log in or create an account to access the platform.")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login to Your Account")
        with st.form("login_form"):
            login_username = st.text_input("Username")
            login_password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Log In")
            
            if submit_login:
                if not login_username or not login_password:
                    st.error("Please provide both username and password.")
                else:
                    with st.session_state['db'].get_session() as db:
                        success, user, msg = AuthManager.authenticate_user(db, login_username, login_password)
                    if success and user:
                        AuthManager.login(user)
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                        
    with tab2:
        st.subheader("Create a New Account")
        with st.form("signup_form"):
            reg_username = st.text_input("Username")
            reg_email = st.text_input("Email")
            reg_password = st.text_input("Password", type="password")
            reg_password_confirm = st.text_input("Confirm Password", type="password")
            submit_signup = st.form_submit_button("Sign Up")
            
            if submit_signup:
                if not reg_username or not reg_email or not reg_password:
                    st.error("Please fill in all fields.")
                elif reg_password != reg_password_confirm:
                    st.error("Passwords do not match.")
                elif len(reg_password) < 6:
                    st.error("Password must be at least 6 characters long.")
                else:
                    with st.session_state['db'].get_session() as db:
                        success, msg = AuthManager.create_user(db, reg_username, reg_email, reg_password)
                    if success:
                        st.success("Account created successfully! You can now switch to the Login tab.")
                    else:
                        st.error(msg)
