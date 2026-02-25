"""Lightweight activity logger for tracking user feature usage."""

import streamlit as st
from datetime import datetime
from typing import Optional


def log_activity(
    db,
    user_id: int,
    feature: str,
    action: str,
    ticker: Optional[str] = None,
    duration_seconds: Optional[float] = None
) -> None:
    """
    Write one activity row to the user_activity table.
    Silently swallows exceptions so it never breaks the calling page.
    """
    if not user_id:
        return
    try:
        from src.models import UserActivity
        session = db.SessionLocal()
        try:
            activity = UserActivity(
                user_id=user_id,
                feature=feature,
                action=action,
                ticker=ticker.upper() if ticker else None,
                duration_seconds=duration_seconds,
                timestamp=datetime.utcnow()
            )
            session.add(activity)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
    except Exception:
        pass  # Never crash the UI over logging


def start_timer(key: str) -> None:
    """
    Record the current time in session_state under a timer key.
    Call this when a user enters a feature/section.
    """
    st.session_state[f"_timer_{key}"] = datetime.utcnow()


def end_timer(key: str) -> Optional[float]:
    """
    Return elapsed seconds since start_timer(key) was called, or None.
    Clears the timer from session_state after reading.
    """
    timer_key = f"_timer_{key}"
    start = st.session_state.pop(timer_key, None)
    if start is None:
        return None
    elapsed = (datetime.utcnow() - start).total_seconds()
    return round(elapsed, 1)


def log_page_visit(db, feature: str) -> None:
    """
    Convenience: log a simple page visit for the current logged-in user.
    Starts a page-level timer so duration can be captured on next visit.
    """
    user_id = st.session_state.get('user_id')
    if not user_id:
        return
    # Log end of previous visit with duration (if timer was running)
    prev_duration = end_timer(f"page_{feature}")
    log_activity(db, user_id, feature, "page_view", duration_seconds=prev_duration)
    # Start timer for this new visit
    start_timer(f"page_{feature}")
