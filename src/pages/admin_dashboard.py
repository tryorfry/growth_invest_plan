import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from src.database import Database
from src.models import User

def show_admin_dashboard(db: Database, session: Session):
    st.title("🛡️ Admin Dashboard")
    st.markdown("Manage registered users, their subscription tiers, and system access.")
    st.divider()

    # Verify authorization again just in case
    if st.session_state.get('user_tier') != 'admin':
        st.error("Unauthorized Access. Admin privileges required.")
        return

    users = session.query(User).all()
    if not users:
        st.info("No users found.")
        return
        
    st.subheader("Manage Users")
    
    # Create an interactive table
    user_data = []
    for user in users:
        user_data.append({
            "ID": user.id,
            "Username": user.username,
            "Email": user.email,
            "Tier": user.tier,
            "Joined": user.created_at.strftime("%Y-%m-%d") if user.created_at else "N/A"
        })
        
    df = pd.DataFrame(user_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.divider()
    st.subheader("Update Subscription Tier")
    col1, col2, col3 = st.columns(3)
    
    # Filter out admin users from being selected for modification
    modifiable_users = [u.username for u in users if u.tier != 'admin']
    
    with col1:
        if not modifiable_users:
            st.info("No modifiable users found.")
            return
        target_username = st.selectbox("Select User", options=modifiable_users)
    with col2:
        target_user = session.query(User).filter(User.username == target_username).first()
        current_tier = target_user.tier if target_user else "free"
        st.metric("Current Tier", current_tier)
    with col3:
        new_tier = st.selectbox("New Tier", options=['free', 'premium'], index=['free', 'premium'].index(current_tier) if current_tier in ['free', 'premium'] else 0)
        
    if st.button("Update Subscription", type="primary"):
        if target_user and current_tier != new_tier:
            target_user.tier = new_tier
            session.commit()
            st.success(f"Successfully updated {target_username} to `{new_tier}` tier!")
            st.rerun()
        elif current_tier == new_tier:
            st.info("No changes made.")

