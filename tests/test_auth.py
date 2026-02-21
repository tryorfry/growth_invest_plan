"""Unit tests for the Authentication module"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base, User
from src.auth import AuthManager
import bcrypt

@pytest.fixture
def test_db():
    """Setup an in-memory SQLite database for testing"""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_hash_password():
    password = "MySecurePassword123!"
    hashed = AuthManager.hash_password(password)
    
    assert hashed != password
    assert isinstance(hashed, str)
    assert len(hashed) > 50 # bcrypt hashes are 60 chars

def test_verify_password():
    password = "MySecurePassword123!"
    hashed = AuthManager.hash_password(password)
    
    assert AuthManager.verify_password(password, hashed) is True
    assert AuthManager.verify_password("WrongPassword!", hashed) is False

def test_create_user(test_db):
    success, msg = AuthManager.create_user(test_db, "testuser", "test@test.com", "password")
    
    assert success is True
    assert msg == "User created successfully"
    
    # Verify DB insertion
    user = test_db.query(User).filter(User.username == "testuser").first()
    assert user is not None
    assert user.email == "test@test.com"
    assert user.tier == "free"

def test_create_duplicate_user(test_db):
    # First creation should succeed
    AuthManager.create_user(test_db, "testuser", "test@test.com", "password")
    
    # Duplicate username
    success1, msg1 = AuthManager.create_user(test_db, "testuser", "different@test.com", "password")
    assert success1 is False
    assert "Username already exists" in msg1
    
    # Duplicate email
    success2, msg2 = AuthManager.create_user(test_db, "diffuser", "test@test.com", "password")
    assert success2 is False
    assert "Email already registered" in msg2

def test_authenticate_user(test_db):
    AuthManager.create_user(test_db, "testuser", "test@test.com", "password")
    
    # Success
    success, user, msg = AuthManager.authenticate_user(test_db, "testuser", "password")
    assert success is True
    assert user.username == "testuser"
    
    # Wrong password
    success, user, msg = AuthManager.authenticate_user(test_db, "testuser", "wrong")
    assert success is False
    assert user is None
    
    # Non-existent user
    success, user, msg = AuthManager.authenticate_user(test_db, "nobody", "password")
    assert success is False
    assert user is None
