"""Fitbit Training Toolkit SDK."""

from .auth.google_auth import GoogleHealthOAuthClient
from .auth.pkce import exchange_code_for_token, get_authorization_url, revoke_token
from .core.base import BaseBiometricProvider
from .core.fitbit import FitbitProvider
from .core.google_health import GoogleHealthProvider

__version__ = "0.2.0"
__all__ = [
    "BaseBiometricProvider",
    "FitbitProvider",
    "GoogleHealthOAuthClient",
    "GoogleHealthProvider",
    "exchange_code_for_token",
    "get_authorization_url",
    "revoke_token",
]
