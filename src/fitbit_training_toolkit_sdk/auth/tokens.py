"""Token persistence and automatic lifecycle manager."""

import json
import logging
import time
from pathlib import Path
from typing import Any

from .pkce import refresh_access_token

log = logging.getLogger(__name__)


class TokenManager:
    """Manages storing, retrieving, and refreshing OAuth2 tokens."""

    def __init__(
        self,
        client_id: str,
        token_path: Path | str | None = None,
        initial_tokens: dict[str, Any] | None = None,
        client_secret: str | None = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_path = Path(token_path) if token_path else None
        self._tokens: dict[str, Any] = initial_tokens or {}

        if self.token_path and self.token_path.exists():
            self._load()

        if initial_tokens and self.token_path:
            self._save()

    def _load(self) -> None:
        if self.token_path and self.token_path.exists():
            with open(self.token_path, "r") as f:
                self._tokens = json.load(f)

    def _save(self) -> None:
        if self.token_path:
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, "w") as f:
                json.dump(self._tokens, f, indent=2)

    def get_valid_access_token(self) -> str:
        """Returns a valid access token, proactively refreshing if within 60s of expiration."""
        if not self._tokens:
            raise ValueError("No tokens available in TokenManager.")

        expires_at = self._tokens.get("expires_at", 0)
        now = time.time()

        if now >= expires_at - 60:
            refresh_token = self._tokens.get("refresh_token")
            if not refresh_token:
                raise ValueError("Access token expired and no refresh_token available.")

            log.info("🔄 Refreshing expired Fitbit access token...")
            new_tokens = refresh_access_token(
                client_id=self.client_id,
                refresh_token=refresh_token,
                client_secret=self.client_secret,
            )
            # Add calculated expires_at
            expires_in = new_tokens.get("expires_in", 28800)
            new_tokens["expires_at"] = time.time() + expires_in
            self._tokens = new_tokens
            self._save()

        return self._tokens["access_token"]
