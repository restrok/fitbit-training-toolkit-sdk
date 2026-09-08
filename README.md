# Fitbit Training Toolkit SDK

Autonomous Python SDK for extracting, normalizing, and analyzing biometric telemetry from the Fitbit Web API.
Designed as a peer to `garmin-training-toolkit-sdk` for multi-device athletic platforms.

## Features
- **OAuth2 PKCE & SSO 2.0:** Secure authorization flow without requiring a client secret for CLI/embedded clients, plus interactive copy-paste token exchange.
- **Canonical Data Normalization:** Standardizes Fitbit activities, intraday heart rate, HRV (RMSSD), and 4-stage sleep architectures into canonical Pydantic models.
- **Auto-Refreshing Token Manager:** Manages token expiry, disk persistence, and silent background refreshes.
- **Mock Testing Harness:** Test downstream analysis workflows completely offline without Fitbit API credentials.

## Installation
```bash
uv pip install -e .
```

## Quickstart (OAuth2 PKCE)
```python
from fitbit_training_toolkit_sdk.auth.pkce import generate_pkce_pair, get_authorization_url, exchange_code_for_token
from fitbit_training_toolkit_sdk.core.fitbit import FitbitProvider

# 1. Generate PKCE parameters and authorization URL
verifier, challenge = generate_pkce_pair()
auth_url = get_authorization_url(client_id="YOUR_CLIENT_ID", code_challenge=challenge)
print(f"Authorize at: {auth_url}")

# 2. Exchange authorization code
tokens = exchange_code_for_token(client_id="YOUR_CLIENT_ID", code=auth_code, code_verifier=verifier)

# 3. Fetch canonical biometrics
provider = FitbitProvider(tokens=tokens)
activities = provider.get_activities(start_date=date(2026, 9, 1), end_date=date(2026, 9, 8))
```
