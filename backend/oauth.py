from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlencode

import httpx
import jwt
from jwt import PyJWKClient

from backend.config import settings

OAuthProvider = Literal["google", "microsoft"]


@dataclass(frozen=True)
class OAuthIdentity:
    email: str
    full_name: str
    provider: OAuthProvider


class OAuthError(Exception):
    def __init__(self, message: str, status_code: int = 401) -> None:
        super().__init__(message)
        self.status_code = status_code


def provider_enabled(provider: OAuthProvider) -> bool:
    if provider == "google":
        return bool(settings.google_client_id.strip())
    return bool(settings.microsoft_client_id.strip())


def oauth_config() -> dict[str, str | bool]:
    google = settings.google_client_id.strip()
    microsoft = settings.microsoft_client_id.strip()
    return {
        "google": bool(google),
        "microsoft": bool(microsoft),
        "google_client_id": google,
        "microsoft_client_id": microsoft,
    }


def verify_oauth_id_token(provider: OAuthProvider, id_token: str) -> OAuthIdentity:
    token = id_token.strip()
    if not token:
        raise OAuthError("Missing identity token.")
    if not provider_enabled(provider):
        raise OAuthError(f"{provider.title()} sign-in is not configured.", status_code=503)
    if provider == "google":
        return _verify_google(token)
    return _verify_microsoft(token)


def _verify_google(id_token: str) -> OAuthIdentity:
    param = "id_token" if id_token.count(".") == 2 else "access_token"
    url = "https://oauth2.googleapis.com/tokeninfo?" + urlencode({param: id_token})
    try:
        response = httpx.get(url, timeout=10.0)
    except httpx.HTTPError as exc:
        raise OAuthError("Could not verify Google token.") from exc
    if response.status_code != 200:
        raise OAuthError("Invalid Google token.")
    claims = response.json()
    audience = str(claims.get("aud") or "")
    if audience != settings.google_client_id.strip():
        raise OAuthError("Invalid Google token audience.")
    email = str(claims.get("email") or "").strip().lower()
    raw_verified = claims.get("email_verified")
    verified = raw_verified is True or str(raw_verified or "").lower() in {"true", "1"}
    if not email or not verified:
        raise OAuthError("Google did not provide a verified email.")
    name = str(claims.get("name") or "").strip()
    if not name:
        given = str(claims.get("given_name") or "").strip()
        family = str(claims.get("family_name") or "").strip()
        name = " ".join(part for part in (given, family) if part)
    if not name and param == "access_token":
        try:
            profile = httpx.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {id_token}"},
                timeout=10.0,
            )
            if profile.status_code == 200:
                body = profile.json()
                name = str(body.get("name") or "").strip()
        except httpx.HTTPError:
            pass
    return OAuthIdentity(email=email, full_name=name or email.split("@")[0], provider="google")


def _verify_microsoft(id_token: str) -> OAuthIdentity:
    tenant = settings.microsoft_tenant_id.strip() or "common"
    client_id = settings.microsoft_client_id.strip()
    jwks_url = f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"
    try:
        jwk_client = PyJWKClient(jwks_url)
        signing_key = jwk_client.get_signing_key_from_jwt(id_token)
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=client_id,
            options={"verify_iss": False},
        )
    except Exception as exc:
        raise OAuthError("Invalid Microsoft token.") from exc
    issuer = str(claims.get("iss") or "")
    if "login.microsoftonline.com" not in issuer and "sts.windows.net" not in issuer:
        raise OAuthError("Invalid Microsoft token issuer.")
    email = str(claims.get("email") or claims.get("preferred_username") or "").strip().lower()
    if not email or "@" not in email:
        raise OAuthError("Microsoft did not provide an email address.")
    name = str(claims.get("name") or "").strip()
    if not name:
        given = str(claims.get("given_name") or "").strip()
        family = str(claims.get("family_name") or "").strip()
        name = " ".join(part for part in (given, family) if part)
    return OAuthIdentity(email=email, full_name=name or email.split("@")[0], provider="microsoft")
