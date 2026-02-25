"""Lightweight activity logger for tracking user feature usage."""

import streamlit as st
from datetime import datetime
from typing import Optional


def _ensure_table(db) -> None:
    """
    Self-healing: create the user_activity table if it doesn't exist.
    This handles running servers that cached init_db() before the new model was added.
    Called lazily on the first log attempt.
    """
    if st.session_state.get('_activity_table_checked'):
        return
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            # Check if table exists (works for both SQLite and Postgres)
            result = conn.execute(text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_name='user_activity'"
            ))
            exists = result.fetchone() is not None
    except Exception:
        # information_schema not available in SQLite — try a different approach
        try:
            from sqlalchemy import inspect
            exists = 'user_activity' in inspect(db.engine).get_table_names()
        except Exception:
            exists = False

    if not exists:
        try:
            from src.models import Base
            Base.metadata.create_all(db.engine)
        except Exception:
            pass

    st.session_state['_activity_table_checked'] = True


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
        _ensure_table(db)
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
        except Exception as e:
            session.rollback()
            # Only log to console; never crash the UI
            print(f"[activity_logger] Failed to log activity: {e}")
        finally:
            session.close()
    except Exception as e:
        print(f"[activity_logger] Outer error: {e}")


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
    Log a page visit for the current logged-in user.
    Only logs once per page load (guards against duplicate logs on every widget rerun).
    """
    user_id = st.session_state.get('user_id')
    if not user_id:
        return

    # Use a per-feature visit counter to deduplicate within a single page session
    visit_key = f"_visited_{feature}"
    already_logged = st.session_state.get(visit_key, False)

    if not already_logged:
        log_activity(db, user_id, feature, "page_view")
        st.session_state[visit_key] = True
        start_timer(f"page_{feature}")
