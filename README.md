# Fitbit Training Toolkit SDK

An open-source Python SDK for extracting, parsing, normalizing, and analyzing Fitbit biometric and endurance telemetry data.

Built following **100% official Fitbit Web API specifications** with modern Python (3.11+), Pydantic v2, and secure OAuth 2.0 PKCE.

---

## 🚀 Key Features

- **OAuth 2.0 PKCE (RFC 7636):** Public-client authorization flow with SHA-256 code challenge, zero client-secret leakage, and RFC 7009 token revocation.
- **Official Scopes Supported (13 Scopes):** `activity`, `cardio_fitness`, `electrocardiogram`, `heartrate`, `location`, `nutrition`, `oxygen_saturation`, `profile`, `respiratory_rate`, `settings`, `sleep`, `temperature`, `weight`.
- **Activity & GPS Normalization:** Parses `/1/user/-/activities/list.json` and TCX GPS streams (`.tcx`) into canonical `Activity` models with 4-zone heart rate distribution (`Out of Range`, `Fat Burn`, `Cardio`, `Peak`).
- **Sleep Normalization (Dual Format):** Native parsing for both modern `stages` (deep, light, REM, wake with 30-sec epochs) and legacy `classic` (asleep, awake, restless with 60-sec epochs).
- **Heart Rate Variability (HRV):** Overnight RMSSD extraction (`dailyRmssd`, `deepRmssd`).
- **Cardio Fitness Score (VO2 Max):** Daily and range queries for cardio fitness estimations.
- **Intraday Heart Rate (1-sec / 1-min):** High-resolution intraday telemetry extraction.
- **Rate Limit Resilience:** Automatic inspection of `Fitbit-Rate-Limit-*` response headers.
- **Offline Simulation:** Deterministic `MockFitbitProvider` for local testing and CI/CD pipelines.

---

## ⚠️ Important Note: Deprecation Roadmap (Google Health API)

Per official announcement on [dev.fitbit.com](https://dev.fitbit.com/build/reference/web-api/):
> *The Fitbit Web APIs are moving to a new, scalable infrastructure. Legacy Fitbit Web APIs are scheduled for deprecation in September 2026. Applications should prepare to migrate to the Google Health API.*

This SDK is engineered with decoupled protocol abstractions (`BaseBiometricProvider`) ensuring a seamless migration path to the Google Health API.

---

## 📦 Installation

```bash
uv pip install -e .
# or with pip
pip install -e .
```

---

## ⚡ Quickstart

### 1. OAuth 2.0 PKCE Flow
```python
from fitbit_training_toolkit_sdk.auth.pkce import generate_pkce_pair, get_authorization_url, exchange_code_for_token

# Step 1: Generate PKCE verifier & challenge
verifier, challenge = generate_pkce_pair()

# Step 2: Generate Authorization URL
auth_url = get_authorization_url(
    client_id="YOUR_FITBIT_CLIENT_ID",
    code_challenge=challenge,
    redirect_uri="http://localhost:8080/callback",
    expires_in=2592000, # 30 days
    prompt="consent"
)
print("Open this URL in your browser:", auth_url)

# Step 3: Exchange authorization code for tokens
tokens = exchange_code_for_token(
    client_id="YOUR_FITBIT_CLIENT_ID",
    code="CODE_RECEIVED_AT_CALLBACK",
    code_verifier=verifier,
    redirect_uri="http://localhost:8080/callback"
)
```

### 2. Querying Biometric Data
```python
from datetime import date
from fitbit_training_toolkit_sdk.core.fitbit import FitbitProvider

provider = FitbitProvider(
    client_id="YOUR_FITBIT_CLIENT_ID",
    token_path="~/.fitbit/tokens.json"
)

# Fetch Activities
activities = provider.get_activities(date(2026, 9, 1), date(2026, 9, 8))
for act in activities:
    print(act.name, act.duration_sec, act.distance_m)

# Fetch Sleep & HRV
sleep = provider.get_sleep_history(date(2026, 9, 1), date(2026, 9, 8))
hrv = provider.get_hrv_history(date(2026, 9, 1), date(2026, 9, 8))
```

---

## 🧪 Testing

```bash
uv run --extra dev pytest -v
uv run --extra dev ruff check
```
