from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from backend.app import app
from tests.conftest import requires_postgres

client = TestClient(app)

TEST_PASSWORD = "Passw0rd!"


def _register(email: str | None = None, full_name: str = "Ada Lovelace") -> dict:
    payload = {
        "full_name": full_name,
        "email": email or f"{uuid.uuid4()}@example.com",
        "password": TEST_PASSWORD,
    }
    response = client.post("/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@requires_postgres
def test_register_login_and_me():
    email = f"{uuid.uuid4()}@example.com"
    registered = _register(email=email, full_name="Grace Hopper")
    assert registered["token_type"] == "bearer"
    assert registered["user"]["email"] == email
    assert registered["user"]["full_name"] == "Grace Hopper"

    me = client.get("/v1/auth/me", headers=auth_headers(registered["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == email

    login = client.post(
        "/v1/auth/login",
        json={"email": email, "password": TEST_PASSWORD, "remember": True},
    )
    assert login.status_code == 200
    assert login.json()["user"]["id"] == registered["user"]["id"]


@requires_postgres
def test_duplicate_email_conflict():
    email = f"{uuid.uuid4()}@example.com"
    _register(email=email)
    again = client.post(
        "/v1/auth/register",
        json={"full_name": "Other", "email": email, "password": TEST_PASSWORD},
    )
    assert again.status_code == 409


@requires_postgres
def test_login_rejects_bad_credentials():
    email = f"{uuid.uuid4()}@example.com"
    _register(email=email)
    response = client.post(
        "/v1/auth/login",
        json={"email": email, "password": "Wrong-pass1!", "remember": False},
    )
    assert response.status_code == 401


@requires_postgres
def test_documents_and_chat_require_auth():
    docs = client.get("/v1/documents")
    assert docs.status_code == 401
    home = client.get("/v1/home")
    assert home.status_code == 401
    chat = client.post("/v1/chat", json={"question": "What skills are on my resume?", "stream": False})
    assert chat.status_code == 401


@requires_postgres
def test_remember_me_issues_longer_lived_token():
    import jwt

    from backend.config import settings

    email = f"{uuid.uuid4()}@example.com"
    _register(email=email)
    short = client.post(
        "/v1/auth/login",
        json={"email": email, "password": TEST_PASSWORD, "remember": False},
    )
    long = client.post(
        "/v1/auth/login",
        json={"email": email, "password": TEST_PASSWORD, "remember": True},
    )
    assert short.status_code == 200
    assert long.status_code == 200
    short_exp = jwt.decode(
        short.json()["access_token"], settings.jwt_secret, algorithms=[settings.jwt_alg]
    )["exp"]
    long_exp = jwt.decode(
        long.json()["access_token"], settings.jwt_secret, algorithms=[settings.jwt_alg]
    )["exp"]
    assert long_exp - short_exp >= 60 * 24 * 20 * 60


@requires_postgres
def test_logout_is_noop():
    response = client.post("/v1/auth/logout")
    assert response.status_code == 204


def test_register_rejects_weak_password():
    response = client.post(
        "/v1/auth/register",
        json={"full_name": "Ada", "email": f"{uuid.uuid4()}@example.com", "password": "password"},
    )
    assert response.status_code == 422
