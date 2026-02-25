"""Admin Dashboard — Activity Tracking & User Management"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from src.database import Database
from src.models import User, UserActivity


# ──────────────────────────────────────────────
# Helper: load activity data
# ──────────────────────────────────────────────

def _load_activity(session: Session, days: int = 30) -> pd.DataFrame:
    """Return all UserActivity rows as a DataFrame, filtered to the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    rows = (
        session.query(
            UserActivity.id,
            UserActivity.user_id,
            User.username,
            UserActivity.feature,
            UserActivity.action,
            UserActivity.ticker,
            UserActivity.duration_seconds,
            UserActivity.timestamp,
        )
        .join(User, User.id == UserActivity.user_id)
        .filter(UserActivity.timestamp >= cutoff)
        .order_by(desc(UserActivity.timestamp))
        .all()
    )
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=[
        "id", "user_id", "username", "feature", "action",
        "ticker", "duration_seconds", "timestamp"
    ])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def _mini_bar(df: pd.DataFrame, x_col: str, y_col: str, title: str, color: str = "#2576d2") -> go.Figure:
    fig = go.Figure(go.Bar(
        x=df[x_col], y=df[y_col],
        marker_color=color,
        text=df[y_col], textposition="outside"
    ))
    fig.update_layout(
        title=title, height=320,
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)")
    )
    return fig


# ──────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────

def show_admin_dashboard(db: Database, session: Session):
    st.title("🛡️ Admin Dashboard")
    st.markdown("Monitor user activity, feature engagement, and manage subscriptions.")
    st.divider()

    # Auth guard
    if st.session_state.get('user_tier') != 'admin':
        st.error("Unauthorized Access. Admin privileges required.")
        return

    # Date range filter (sidebar-style)
    col_filter1, col_filter2 = st.columns([3, 1])
    with col_filter2:
        days = st.selectbox("Data Window", [7, 14, 30, 60, 90], index=2, key="admin_days")

    # Load activity data
    df = _load_activity(session, days=days)
    all_users = session.query(User).all()
    has_data = not df.empty

    # ── 6 Tabs ──────────────────────────────────
    tab_overview, tab_features, tab_users, tab_tickers, tab_raw, tab_manage = st.tabs([
        "📊 Overview",
        "⚙️ Feature Usage",
        "👤 User Breakdown",
        "📈 Ticker Popularity",
        "🗂️ Raw Activity Log",
        "🔧 User Management",
    ])

    # ─────────────────────────────────
    # TAB 1: Overview
    # ─────────────────────────────────
    with tab_overview:
        st.subheader(f"Platform Overview — Last {days} Days")

        total_users = len(all_users)
        active_users = df["user_id"].nunique() if has_data else 0
        total_events = len(df) if has_data else 0
        top_ticker = df["ticker"].mode()[0] if has_data and df["ticker"].notna().any() else "N/A"

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Registered Users", total_users)
        m2.metric("Active Users (Period)", active_users,
                  delta=f"{active_users}/{total_users} active",
                  delta_color="normal" if active_users > 0 else "off")
        m3.metric("Total Events Logged", f"{total_events:,}")
        m4.metric("Most Searched Ticker", top_ticker)

        if has_data:
            st.divider()
            st.subheader("Daily Activity Trend")
            daily = (
                df.groupby(df["timestamp"].dt.date)
                .size()
                .reset_index(name="events")
                .rename(columns={"timestamp": "date"})
            )
            fig_trend = go.Figure(go.Scatter(
                x=daily["date"], y=daily["events"],
                mode="lines+markers",
                line=dict(color="#2576d2", width=2),
                fill="tozeroy",
                fillcolor="rgba(37, 118, 210, 0.15)"
            ))
            fig_trend.update_layout(
                height=280, margin=dict(l=10, r=10, t=20, b=10),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                xaxis=dict(showgrid=False, type="date"),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.1)")
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No activity logged yet. Activity will appear here once users interact with the app.")

    # ─────────────────────────────────
    # TAB 2: Feature Usage
    # ─────────────────────────────────
    with tab_features:
        st.subheader("Feature Engagement Breakdown")

        if has_data:
            feature_stats = (
                df.groupby("feature")
                .agg(
                    total_events=("id", "count"),
                    unique_users=("user_id", "nunique"),
                    avg_duration=("duration_seconds", "mean")
                )
                .reset_index()
                .sort_values("total_events", ascending=False)
            )
            feature_stats["avg_duration"] = feature_stats["avg_duration"].apply(
                lambda x: f"{x:.0f}s" if pd.notna(x) else "N/A"
            )

            # Bar chart
            fig_feat = _mini_bar(feature_stats, "feature", "total_events",
                                 "Total Events per Feature", "#00C853")
            st.plotly_chart(fig_feat, use_container_width=True)

            # Table
            st.markdown("### Detailed Stats")
            st.dataframe(
                feature_stats.rename(columns={
                    "feature": "Feature",
                    "total_events": "Total Events",
                    "unique_users": "Unique Users",
                    "avg_duration": "Avg Duration"
                }),
                use_container_width=True, hide_index=True
            )

            # Action breakdown within each feature
            st.divider()
            st.markdown("### Action Breakdown by Feature")
            selected_feature = st.selectbox(
                "Select Feature",
                options=df["feature"].unique().tolist(),
                key="admin_feat_select"
            )
            action_df = (
                df[df["feature"] == selected_feature]
                .groupby("action")
                .size()
                .reset_index(name="count")
                .sort_values("count", ascending=False)
            )
            fig_act = _mini_bar(action_df, "action", "count",
                                f"Actions in {selected_feature}", "#FF6D00")
            st.plotly_chart(fig_act, use_container_width=True)
        else:
            st.info("No activity data available.")

    # ─────────────────────────────────
    # TAB 3: User Breakdown
    # ─────────────────────────────────
    with tab_users:
        st.subheader("Per-User Activity Summary")

        if has_data:
            user_stats = (
                df.groupby(["user_id", "username"])
                .agg(
                    total_events=("id", "count"),
                    unique_features=("feature", "nunique"),
                    last_active=("timestamp", "max"),
                    top_feature=("feature", lambda x: x.mode()[0])
                )
                .reset_index()
                .sort_values("total_events", ascending=False)
            )
            user_stats["last_active"] = user_stats["last_active"].dt.strftime("%Y-%m-%d %H:%M")

            st.dataframe(
                user_stats[["username", "total_events", "unique_features", "top_feature", "last_active"]]
                .rename(columns={
                    "username": "User",
                    "total_events": "Events",
                    "unique_features": "Features Used",
                    "top_feature": "Favourite Feature",
                    "last_active": "Last Active"
                }),
                use_container_width=True, hide_index=True
            )

            st.divider()
            st.markdown("### Drill Down — Individual User Activity")
            selected_user = st.selectbox(
                "Select User",
                options=user_stats["username"].tolist(),
                key="admin_user_select"
            )
            user_df = df[df["username"] == selected_user].copy()
            user_df["timestamp"] = user_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
            st.dataframe(
                user_df[["timestamp", "feature", "action", "ticker", "duration_seconds"]].rename(columns={
                    "timestamp": "Time",
                    "feature": "Feature",
                    "action": "Action",
                    "ticker": "Ticker",
                    "duration_seconds": "Duration (s)"
                }),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No activity data available.")

    # ─────────────────────────────────
    # TAB 4: Ticker Popularity
    # ─────────────────────────────────
    with tab_tickers:
        st.subheader("Most Searched Tickers")

        if has_data and df["ticker"].notna().any():
            ticker_df = (
                df[df["ticker"].notna()]
                .groupby("ticker")
                .size()
                .reset_index(name="searches")
                .sort_values("searches", ascending=False)
                .head(20)
            )
            fig_tick = _mini_bar(ticker_df, "ticker", "searches",
                                 "Top 20 Tickers by Search Count", "#AA00FF")
            st.plotly_chart(fig_tick, use_container_width=True)

            st.dataframe(
                ticker_df.rename(columns={"ticker": "Ticker", "searches": "Searches"}),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No ticker search data available yet.")

    # ─────────────────────────────────
    # TAB 5: Raw Activity Log
    # ─────────────────────────────────
    with tab_raw:
        st.subheader("Raw Activity Log")

        if has_data:
            # Filters
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                f_user = st.selectbox("Filter by User", ["All"] + df["username"].unique().tolist(), key="raw_user")
            with fc2:
                f_feat = st.selectbox("Filter by Feature", ["All"] + df["feature"].unique().tolist(), key="raw_feat")
            with fc3:
                f_ticker = st.text_input("Filter by Ticker", key="raw_ticker").strip().upper()

            filtered = df.copy()
            if f_user != "All":
                filtered = filtered[filtered["username"] == f_user]
            if f_feat != "All":
                filtered = filtered[filtered["feature"] == f_feat]
            if f_ticker:
                filtered = filtered[filtered["ticker"].str.upper().str.contains(f_ticker, na=False)]

            st.caption(f"Showing {len(filtered):,} of {len(df):,} events")

            display = filtered[["timestamp", "username", "feature", "action", "ticker", "duration_seconds"]].copy()
            display["timestamp"] = display["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
            st.dataframe(
                display.rename(columns={
                    "timestamp": "Time", "username": "User",
                    "feature": "Feature", "action": "Action",
                    "ticker": "Ticker", "duration_seconds": "Duration (s)"
                }),
                use_container_width=True, hide_index=True, height=400
            )

            # CSV Export
            csv = filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"user_activity_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No activity records found for the selected period.")

    # ─────────────────────────────────
    # TAB 6: User Management (existing)
    # ─────────────────────────────────
    with tab_manage:
        st.subheader("Manage Users")

        users = session.query(User).all()
        if not users:
            st.info("No users found.")
            return

        user_data = []
        for user in users:
            event_count = df[df["user_id"] == user.id].shape[0] if has_data else 0
            user_data.append({
                "ID": user.id,
                "Username": user.username,
                "Email": user.email,
                "Tier": user.tier,
                "Events (Period)": event_count,
                "Joined": user.created_at.strftime("%Y-%m-%d") if user.created_at else "N/A"
            })

        st.dataframe(pd.DataFrame(user_data), use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Update Subscription Tier")
        col1, col2, col3 = st.columns(3)
        modifiable_users = [u.username for u in users if u.tier != 'admin']

        with col1:
            if not modifiable_users:
                st.info("No modifiable users found.")
                return
            target_username = st.selectbox("Select User", options=modifiable_users, key="mgmt_user")
        with col2:
            target_user = session.query(User).filter(User.username == target_username).first()
            current_tier = target_user.tier if target_user else "free"
            st.metric("Current Tier", current_tier)
        with col3:
            new_tier = st.selectbox(
                "New Tier", options=['free', 'premium'],
                index=['free', 'premium'].index(current_tier) if current_tier in ['free', 'premium'] else 0,
                key="mgmt_tier"
            )

        if st.button("Update Subscription", type="primary", key="mgmt_update"):
            if target_user and current_tier != new_tier:
                target_user.tier = new_tier
                session.commit()
                st.success(f"✅ Updated {target_username} to `{new_tier}` tier!")
                st.rerun()
            elif current_tier == new_tier:
                st.info("No changes made.")
