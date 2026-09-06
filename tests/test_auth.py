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


def test_oauth_config_reflects_client_ids(monkeypatch):
    from backend.config import settings

    monkeypatch.setattr(settings, "google_client_id", "")
    monkeypatch.setattr(settings, "microsoft_client_id", "ms-app")
    response = client.get("/v1/auth/oauth/config")
    assert response.status_code == 200
    assert response.json() == {
        "google": False,
        "microsoft": True,
        "google_client_id": "",
        "microsoft_client_id": "ms-app",
    }


def test_oauth_unconfigured_is_503(monkeypatch):
    from backend.config import settings

    monkeypatch.setattr(settings, "google_client_id", "")
    response = client.post(
        "/v1/auth/oauth",
        json={"provider": "google", "id_token": "fake.token", "remember": False},
    )
    assert response.status_code == 503


def test_oauth_invalid_token_is_401(monkeypatch):
    from backend.config import settings
    from backend.oauth import OAuthError
    import backend.routers.auth as auth_router

    monkeypatch.setattr(settings, "google_client_id", "google-client")

    def boom(_provider, _token):
        raise OAuthError("Invalid Google token.")

    monkeypatch.setattr(auth_router, "verify_oauth_id_token", boom)
    response = client.post(
        "/v1/auth/oauth",
        json={"provider": "google", "id_token": "bad", "remember": False},
    )
    assert response.status_code == 401


@requires_postgres
def test_oauth_creates_user(monkeypatch):
    from backend.config import settings
    from backend.oauth import OAuthIdentity
    import backend.routers.auth as auth_router

    email = f"{uuid.uuid4()}@example.com"
    monkeypatch.setattr(settings, "google_client_id", "google-client")
    monkeypatch.setattr(
        auth_router,
        "verify_oauth_id_token",
        lambda _provider, _token: OAuthIdentity(email=email, full_name="OAuth User", provider="google"),
    )
    response = client.post(
        "/v1/auth/oauth",
        json={"provider": "google", "id_token": "valid", "remember": True},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["user"]["email"] == email
    assert body["user"]["full_name"] == "OAuth User"
    me = client.get("/v1/auth/me", headers=auth_headers(body["access_token"]))
    assert me.status_code == 200


@requires_postgres
def test_oauth_logs_in_existing_email(monkeypatch):
    from backend.config import settings
    from backend.oauth import OAuthIdentity
    import backend.routers.auth as auth_router

    email = f"{uuid.uuid4()}@example.com"
    registered = _register(email=email, full_name="Existing User")
    monkeypatch.setattr(settings, "microsoft_client_id", "ms-client")
    monkeypatch.setattr(
        auth_router,
        "verify_oauth_id_token",
        lambda _provider, _token: OAuthIdentity(email=email, full_name="Microsoft Name", provider="microsoft"),
    )
    response = client.post(
        "/v1/auth/oauth",
        json={"provider": "microsoft", "id_token": "valid", "remember": False},
    )
    assert response.status_code == 200, response.text
    assert response.json()["user"]["id"] == registered["user"]["id"]
    assert response.json()["user"]["full_name"] == "Existing User"
