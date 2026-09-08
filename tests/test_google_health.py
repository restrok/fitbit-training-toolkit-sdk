"""Unit tests for GoogleHealthOAuthClient and GoogleHealthProvider."""

import urllib.parse
from datetime import date
from unittest.mock import MagicMock, patch

from fitbit_training_toolkit_sdk.auth.google_auth import (
    GOOGLE_HEALTH_DEFAULT_SCOPES,
    GoogleHealthOAuthClient,
    generate_code_challenge,
    generate_code_verifier,
)
from fitbit_training_toolkit_sdk.core.google_health import GoogleHealthProvider


def test_google_pkce_generation():
    verifier = generate_code_verifier()
    challenge = generate_code_challenge(verifier)
    assert len(verifier) >= 43
    assert len(challenge) >= 43
    assert "=" not in challenge


def test_google_auth_url():
    client = GoogleHealthOAuthClient(client_id="test_client_id")
    url, _verifier = client.get_authorization_url()
    assert "https://accounts.google.com/o/oauth2/v2/auth" in url
    assert "client_id=test_client_id" in url
    assert "code_challenge=" in url
    assert "code_challenge_method=S256" in url
    decoded_url = urllib.parse.unquote(url)
    for scope in GOOGLE_HEALTH_DEFAULT_SCOPES[:2]:
        assert scope in decoded_url


@patch("httpx.Client.post")
def test_google_token_exchange(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "access_token": "mock_google_access_token",
        "refresh_token": "mock_google_refresh_token",
        "expires_in": 3600,
        "token_type": "Bearer",
    }
    mock_post.return_value = mock_resp

    client = GoogleHealthOAuthClient(client_id="test_client_id")
    tokens = client.exchange_code_for_tokens(code="auth_code_123", code_verifier="verifier_456")
    assert tokens["access_token"] == "mock_google_access_token"
    assert tokens["refresh_token"] == "mock_google_refresh_token"


@patch("httpx.Client.get")
def test_google_health_provider_activities(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "sessions": [
            {
                "id": "session_fitbit_air_01",
                "activityType": "running",
                "name": "Morning Delta Run",
                "startTime": "2026-09-08T07:00:00+00:00",
                "durationMillis": 3600000,
                "distanceMeters": 10000.0,
                "averageHeartRateBpm": 152,
                "maxHeartRateBpm": 174,
                "calories": 720.0,
            }
        ]
    }
    mock_get.return_value = mock_resp

    tokens = {"access_token": "mock_valid", "expires_at": 9999999999}
    provider = GoogleHealthProvider(client_id="test_cid", tokens=tokens)

    activities = provider.get_activities(date(2026, 9, 8), date(2026, 9, 8))
    assert len(activities) == 1
    act = activities[0]
    assert act.id == "session_fitbit_air_01"
    assert act.name == "Morning Delta Run"
    assert act.duration_sec == 3600.0
    assert act.distance_m == 10000.0
    assert act.avg_hr == 152.0


@patch("httpx.Client.get")
def test_google_health_provider_telemetry(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "samples": [
            {"time": "2026-09-08T07:01:00+00:00", "bpm": 140, "cadence": 178},
            {"time": "2026-09-08T07:02:00+00:00", "bpm": 145, "cadence": 180},
        ]
    }
    mock_get.return_value = mock_resp

    tokens = {"access_token": "mock_valid", "expires_at": 9999999999}
    provider = GoogleHealthProvider(client_id="test_cid", tokens=tokens)

    telem = provider.get_telemetry("session_fitbit_air_01")
    assert telem.activity_id == "session_fitbit_air_01"
    assert len(telem.points) == 2
    assert telem.points[0].heart_rate == 140
    assert telem.points[1].cadence == 180


@patch("httpx.Client.get")
def test_google_health_provider_daily_physiology(mock_get):
    # Mock HRV and Sleep responses
    def side_effect(url, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        if "hrv" in url:
            resp.json.return_value = {
                "hrvMetrics": [{"date": "2026-09-08", "rmssd": 44.5}]
            }
        elif "sleep" in url:
            resp.json.return_value = {
                "sleepSessions": [
                    {
                        "date": "2026-09-08",
                        "durationMillis": 28800000,
                        "stages": {"deepMillis": 7200000, "remMillis": 7200000},
                        "efficiencyScore": 88,
                    }
                ]
            }
        else:
            resp.json.return_value = {}
        return resp

    mock_get.side_effect = side_effect
    tokens = {"access_token": "mock_valid", "expires_at": 9999999999}
    provider = GoogleHealthProvider(client_id="test_cid", tokens=tokens)

    phys = provider.get_daily_physiology(date(2026, 9, 8), date(2026, 9, 8))
    assert len(phys) == 1
    p = phys[0]
    assert p.date == "2026-09-08"
    assert p.hrv_rmssd == 44.5
    assert p.sleep_score == 88
