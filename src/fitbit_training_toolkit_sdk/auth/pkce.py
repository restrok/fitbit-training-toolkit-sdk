"""OAuth 2.0 PKCE (Proof Key for Code Exchange) utilities for Fitbit Web API."""

import base64
import hashlib
import secrets
from urllib.parse import urlencode

import httpx

FITBIT_AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
FITBIT_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
DEFAULT_SCOPES = [
    "activity",
    "heartrate",
    "location",
    "nutrition",
    "profile",
    "settings",
    "sleep",
    "weight",
]


def generate_pkce_pair() -> tuple[str, str]:
    """Generates a code_verifier and code_challenge tuple according to RFC 7636."""
    code_verifier = secrets.token_urlsafe(64)
    sha256_hash = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(sha256_hash).decode("ascii").rstrip("=")
    return code_verifier, code_challenge


def get_authorization_url(
    client_id: str,
    code_challenge: str,
    redirect_uri: str = "http://localhost:8080/callback",
    scopes: list[str] | None = None,
    state: str | None = None,
) -> str:
    """Constructs the authorization URL for user consent with PKCE."""
    params = {
        "client_id": client_id,
        "response_type": "code",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "scope": " ".join(scopes or DEFAULT_SCOPES),
        "redirect_uri": redirect_uri,
        "state": state or secrets.token_urlsafe(16),
    }
    return f"{FITBIT_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_token(
    client_id: str,
    code: str,
    code_verifier: str,
    redirect_uri: str = "http://localhost:8080/callback",
    client_secret: str | None = None,
) -> dict:
    """Exchanges the authorization code and verifier for access and refresh tokens."""
    data = {
        "client_id": client_id,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    if client_secret:
        auth_str = f"{client_id}:{client_secret}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        headers["Authorization"] = f"Basic {encoded_auth}"

    response = httpx.post(FITBIT_TOKEN_URL, data=data, headers=headers)
    response.raise_for_status()
    return response.json()


def refresh_access_token(
    client_id: str,
    refresh_token: str,
    client_secret: str | None = None,
) -> dict:
    """Refreshes an expired access token using the refresh token."""
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    if client_secret:
        auth_str = f"{client_id}:{client_secret}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        headers["Authorization"] = f"Basic {encoded_auth}"

    response = httpx.post(FITBIT_TOKEN_URL, data=data, headers=headers)
    response.raise_for_status()
    return response.json()
