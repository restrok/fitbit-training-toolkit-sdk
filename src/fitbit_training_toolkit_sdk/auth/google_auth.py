"""OAuth 2.0 PKCE authentication flow for Google Health API.

Conforms to official Google Identity & Google Health API specification:
https://developers.google.com/identity/protocols/oauth2/native-app
"""

import base64
import hashlib
import secrets
import urllib.parse
from typing import Any

import httpx

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"

GOOGLE_HEALTH_DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/health.activity.read",
    "https://www.googleapis.com/auth/health.sleep.read",
    "https://www.googleapis.com/auth/health.heart_rate.read",
    "https://www.googleapis.com/auth/health.body.read",
    "openid",
    "profile",
]


def generate_code_verifier(length: int = 64) -> str:
    """Generates a cryptographically random code_verifier string."""
    return secrets.token_urlsafe(length)[:128]


def generate_code_challenge(verifier: str) -> str:
    """Generates an RFC 7636 S256 code_challenge."""
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("utf-8")
    return challenge.replace("=", "")


class GoogleHealthOAuthClient:
    """Google Health API OAuth 2.0 PKCE Client."""

    def __init__(
        self,
        client_id: str,
        redirect_uri: str = "http://localhost:8080/callback",
        client_secret: str | None = None,
        scopes: list[str] | None = None,
    ):
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.client_secret = client_secret
        self.scopes = scopes or GOOGLE_HEALTH_DEFAULT_SCOPES

    def get_authorization_url(self, state: str | None = None) -> tuple[str, str]:
        """Generates Google OAuth 2.0 authorization URL with PKCE.

        Returns:
            tuple of (auth_url, code_verifier)
        """
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        state_val = state or secrets.token_urlsafe(16)

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "redirect_uri": self.redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "state": state_val,
            "access_type": "offline",
            "prompt": "consent",
        }
        url = f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
        return url, code_verifier

    def exchange_code_for_tokens(self, code: str, code_verifier: str) -> dict[str, Any]:
        """Exchanges authorization code and PKCE verifier for Google tokens."""
        data = {
            "client_id": self.client_id,
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": code_verifier,
            "redirect_uri": self.redirect_uri,
        }
        if self.client_secret:
            data["client_secret"] = self.client_secret

        with httpx.Client() as client:
            resp = client.post(GOOGLE_TOKEN_URL, data=data)
            resp.raise_for_status()
            return resp.json()

    def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """Refreshes access token using refresh_token."""
        data = {
            "client_id": self.client_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        if self.client_secret:
            data["client_secret"] = self.client_secret

        with httpx.Client() as client:
            resp = client.post(GOOGLE_TOKEN_URL, data=data)
            resp.raise_for_status()
            return resp.json()

    def revoke_token(self, token: str) -> bool:
        """Revokes an active Google access or refresh token."""
        try:
            with httpx.Client() as client:
                resp = client.post(GOOGLE_REVOKE_URL, params={"token": token})
                return resp.status_code == 200
        except httpx.HTTPError:
            return False
