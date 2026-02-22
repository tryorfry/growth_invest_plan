"""Authentication and user management module"""

import bcrypt
from sqlalchemy.orm import Session
from src.models import User
import streamlit as st

class AuthManager:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password with bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def create_user(db_session: Session, username: str, email: str, password: str, tier: str = 'free') -> tuple[bool, str]:
        """Create a new user. Returns (success, message)"""
        # Check if user exists
        if db_session.query(User).filter(User.username == username).first():
            return False, "Username already exists"
            
        if db_session.query(User).filter(User.email == email).first():
            return False, "Email already registered"
            
        hashed_pw = AuthManager.hash_password(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_pw,
            tier=tier
        )
        
        try:
            db_session.add(new_user)
            db_session.commit()
            return True, "User created successfully"
        except Exception as e:
            db_session.rollback()
            return False, f"Database error: {str(e)}"

    @staticmethod
    def seed_admin(db_session: Session):
        """Seed an admin user from environment variables if no admin exists"""
        import os
        admin_user = os.getenv("ADMIN_USERNAME", "admin")
        admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        
        # Check if any admin exists
        existing_admin = db_session.query(User).filter(User.tier == 'admin').first()
        if not existing_admin:
            # Check if username is taken
            existing_user = db_session.query(User).filter(User.username == admin_user).first()
            if not existing_user:
                AuthManager.create_user(
                    db_session, 
                    username=admin_user, 
                    email=admin_email, 
                    password=admin_pass, 
                    tier='admin'
                )

    @staticmethod
    def authenticate_user(db_session: Session, username: str, password: str) -> tuple[bool, User, str]:
        """Authenticate a user. Returns (success, user_obj, message)"""
        user = db_session.query(User).filter(User.username == username).first()
        
        if not user:
            return False, None, "Invalid username or password"
            
        if not AuthManager.verify_password(password, user.password_hash):
            return False, None, "Invalid username or password"
            
        return True, user, "Login successful"

    @staticmethod
    def init_session_state():
        """Initialize authentication state in Streamlit"""
        if 'authenticated' not in st.session_state:
            st.session_state['authenticated'] = False
        if 'user_id' not in st.session_state:
            st.session_state['user_id'] = None
        if 'username' not in st.session_state:
            st.session_state['username'] = None
        if 'user_tier' not in st.session_state:
            st.session_state['user_tier'] = None

    @staticmethod
    def login(user: User):
        """Set session state for logged in user"""
        st.session_state['authenticated'] = True
        st.session_state['user_id'] = user.id
        st.session_state['username'] = user.username
        st.session_state['user_tier'] = user.tier

    @staticmethod
    def logout():
        """Clear session state"""
        st.session_state['authenticated'] = False
        st.session_state['user_id'] = None
        st.session_state['username'] = None
        st.session_state['user_tier'] = None
        # Rerun to refresh the UI
        st.rerun()

    @staticmethod
    def is_authenticated() -> bool:
        """Check if current session is authenticated"""
        return st.session_state.get('authenticated', False)
