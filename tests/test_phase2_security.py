import base64
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from backend.app import create_app, db
from backend.app.models import AuditLog, User
from backend.app.security.encryption import decrypt_data, encrypt_data
from backend.app.security.jwt import create_token
from backend.app.security.passwords import hash_password, verify_password
from backend.app.security.rate_limit import reset_rate_limits
from backend.app.security.validation import (
    require_blood_group,
    require_positive_id,
    require_positive_units,
    require_urgency,
)


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-app-secret"
    JWT_SECRET_KEY = "test-access-secret"
    JWT_REFRESH_SECRET_KEY = "test-refresh-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ORIGINS = ["http://localhost:5173"]
    JWT_ACCESS_EXPIRES_SECONDS = 900
    JWT_REFRESH_EXPIRES_SECONDS = 604800
    RATE_LIMIT_WINDOW_SECONDS = 60
    RATE_LIMIT_LOGIN = 5
    RATE_LIMIT_REGISTER = 3
    RATE_LIMIT_REFRESH = 10


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_KEY", base64.urlsafe_b64encode(b"x" * 32).decode("ascii"))
    reset_rate_limits()
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        db.session.add_all([
            User(email="admin@example.com", password_hash=hash_password("AdminPassword!123"), role="ADMIN", full_name="Admin User"),
            User(email="user@example.com", password_hash=hash_password("UserPassword!123"), role="USER", full_name="User Example"),
        ])
        db.session.commit()
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()
    reset_rate_limits()


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email="user@example.com", password="UserPassword!123"):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    return response, response.get_json().get("access_token") if response.is_json else None


def test_valid_login_returns_tokens_without_hash(client):
    response, access_token = login(client)
    body = response.get_json()
    assert response.status_code == 200
    assert access_token
    assert body["user"]["role"] == "USER"
    assert "password_hash" not in body
    assert "password" not in body


def test_invalid_password_and_nonexistent_user_are_generic(client):
    invalid = client.post("/api/auth/login", json={"email": "user@example.com", "password": "WrongPassword!123"})
    missing = client.post("/api/auth/login", json={"email": "missing@example.com", "password": "WrongPassword!123"})
    assert invalid.status_code == missing.status_code == 401
    assert invalid.get_json()["error"]["message"] == missing.get_json()["error"]["message"]


def test_register_hashes_password_and_rejects_privileged_role(client, app):
    response = client.post("/api/auth/register", json={"email": "new@example.com", "password": "NewPassword!123", "full_name": "New User"})
    assert response.status_code == 201
    with app.app_context():
        user = User.query.filter_by(email="new@example.com").one()
        assert user.password_hash != "NewPassword!123"
        assert verify_password("NewPassword!123", user.password_hash)
    forbidden_role = client.post("/api/auth/register", json={"email": "admin2@example.com", "password": "NewPassword!123", "full_name": "Admin Attempt", "role": "ADMIN"})
    assert forbidden_role.status_code == 400


def test_protected_endpoint_requires_token_and_invalid_token_is_rejected(client):
    assert client.get("/api/auth/me").status_code == 401
    invalid = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"})
    assert invalid.status_code == 401
    assert "traceback" not in invalid.get_data(as_text=True).lower()


def test_expired_token_is_rejected(client, app):
    with app.app_context():
        user = User.query.filter_by(email="user@example.com").one()
        token = jwt.encode({"sub": str(user.id), "type": "access", "jti": "expired-jti", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}, TestConfig.JWT_SECRET_KEY, algorithm="HS256")
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_rbac_allows_admin_and_denies_user(client):
    _, admin_token = login(client, "admin@example.com", "AdminPassword!123")
    _, user_token = login(client)
    assert client.get("/api/auth/admin-check", headers={"Authorization": f"Bearer {admin_token}"}).status_code == 200
    assert client.get("/api/auth/admin-check", headers={"Authorization": f"Bearer {user_token}"}).status_code == 403


def test_logout_revokes_access_token(client):
    response, token = login(client)
    refresh_token = response.get_json()["refresh_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post("/api/auth/logout", headers=headers, json={"refresh_token": refresh_token}).status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    assert client.post("/api/auth/refresh", json={"refresh_token": refresh_token}).status_code == 401


def test_refresh_token_issues_access_token(client):
    response, _ = login(client)
    refresh_token = response.get_json()["refresh_token"]
    refreshed = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refreshed.status_code == 200
    assert refreshed.get_json()["access_token"]


def test_encryption_round_trip_uses_unique_ciphertext_and_authenticates(monkeypatch):
    monkeypatch.setenv("ENCRYPTION_KEY", base64.urlsafe_b64encode(b"y" * 32).decode("ascii"))
    first = encrypt_data("sensitive phone number")
    second = encrypt_data("sensitive phone number")
    assert first != second
    assert decrypt_data(first) == "sensitive phone number"
    tampered = first[:-2] + ("AA" if first[-2:] != "AA" else "BB")
    with pytest.raises(ValueError):
        decrypt_data(tampered)


def test_validation_rejects_impossible_values():
    with pytest.raises(ValueError):
        require_blood_group("X+")
    with pytest.raises(ValueError):
        require_positive_units(0)
    with pytest.raises(ValueError):
        require_urgency("URGENT")
    with pytest.raises(ValueError):
        require_positive_id(-1, "hospital_id")


def test_login_rate_limit_is_enforced(client):
    for _ in range(5):
        response = client.post("/api/auth/login", json={"email": "user@example.com", "password": "WrongPassword!123"})
        assert response.status_code == 401
    limited = client.post("/api/auth/login", json={"email": "user@example.com", "password": "WrongPassword!123"})
    assert limited.status_code == 429


def test_security_headers_and_audit_event(client, app):
    response, _ = login(client)
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "default-src" in response.headers["Content-Security-Policy"]
    with app.app_context():
        assert AuditLog.query.filter_by(action="LOGIN_SUCCESS").count() == 1
