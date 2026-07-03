import os
# Force SQLite fallback for test execution
os.environ["DATABASE_URL"] = ""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.utils.database import Base, SessionLocal, engine
from app.models.user import User

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    # Clear users first
    db = SessionLocal()
    try:
        db.query(User).delete()
        db.commit()
    finally:
        db.close()
    yield

def test_signup_and_login():
    # Test Signup
    res = client.post("/api/v1/auth/signup", json={"email": "test@example.com", "password": "securepassword"})
    assert res.status_code == 200
    assert res.json()["email"] == "test@example.com"
    
    # Test Signup duplicate
    res = client.post("/api/v1/auth/signup", json={"email": "test@example.com", "password": "securepassword"})
    assert res.status_code == 400
    
    # Test Login
    res = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "securepassword"})
    assert res.status_code == 200
    tokens = res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    
    # Test Login failure
    res = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "wrongpassword"})
    assert res.status_code == 401

def test_token_refresh():
    # Setup user
    client.post("/api/v1/auth/signup", json={"email": "refresh@example.com", "password": "securepassword"})
    login_res = client.post("/api/v1/auth/login", json={"email": "refresh@example.com", "password": "securepassword"})
    tokens = login_res.json()
    
    # Refresh token
    refresh_res = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
