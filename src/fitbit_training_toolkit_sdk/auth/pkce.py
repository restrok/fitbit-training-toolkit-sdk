"""OAuth 2.0 PKCE (Proof Key for Code Exchange) utilities for Fitbit Web API.

Conforms to RFC 7636 and official Fitbit Web API Authorization documentation:
https://dev.fitbit.com/build/reference/web-api/authorization/
"""

import base64
import hashlib
import secrets
from urllib.parse import urlencode

import httpx

FITBIT_AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
FITBIT_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
FITBIT_REVOKE_URL = "https://api.fitbit.com/oauth2/revoke"

# Complete official scopes according to dev.fitbit.com
DEFAULT_SCOPES = [
    "activity",
    "cardio_fitness",
    "electrocardiogram",
    "heartrate",
    "location",
    "nutrition",
    "oxygen_saturation",
    "profile",
    "respiratory_rate",
    "settings",
    "sleep",
    "temperature",
    "weight",
]


def generate_pkce_pair() -> tuple[str, str]:
    """Generates a code_verifier and code_challenge tuple according to RFC 7636.

    code_verifier is a cryptographically random string (43-128 characters).
    code_challenge is the Base64URL-encoded SHA-256 hash without padding.
    """
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
    expires_in: int | None = None,
    prompt: str | None = None,
) -> str:
    """Constructs the authorization URL for user consent with PKCE.

    Supports official parameters:
      - response_type=code (mandatory)
      - client_id (mandatory)
      - code_challenge & code_challenge_method=S256 (mandatory for PKCE)
      - scope (space-delimited)
      - redirect_uri
      - state (CSRF mitigation)
      - expires_in (seconds, e.g. 604800 for 7 days or 2592000 for 30 days)
      - prompt (e.g. 'consent' to force user consent dialog)
    """
    params: dict[str, str] = {
        "client_id": client_id,
        "response_type": "code",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "scope": " ".join(scopes or DEFAULT_SCOPES),
        "redirect_uri": redirect_uri,
        "state": state or secrets.token_urlsafe(16),
    }
    if expires_in is not None:
        params["expires_in"] = str(expires_in)
    if prompt:
        params["prompt"] = prompt

    return f"{FITBIT_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_token(
    client_id: str,
    code: str,
    code_verifier: str,
    redirect_uri: str = "http://localhost:8080/callback",
    client_secret: str | None = None,
) -> dict:
    """Exchanges the authorization code and verifier for access and refresh tokens.

    For public clients using PKCE, client_id is passed in the POST body without Basic Auth.
    If client_secret is provided (confidential client), uses Authorization: Basic.
    """
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


def revoke_token(
    client_id: str,
    token: str,
    client_secret: str | None = None,
) -> bool:
    """Revokes an access token or refresh token per RFC 7009 / Fitbit Web API.

    When a token is revoked, all tokens and sessions for that user and application
    are invalidated. HTTP 200 signifies success. HTTP 404 indicates the token
    was already invalid/not found and can safely be discarded.
    """
    data = {"token": token}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    if client_secret:
        auth_str = f"{client_id}:{client_secret}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        headers["Authorization"] = f"Basic {encoded_auth}"
    else:
        data["client_id"] = client_id

    response = httpx.post(FITBIT_REVOKE_URL, data=data, headers=headers)
    if response.status_code in (200, 404):
        return True
    response.raise_for_status()
    return True
