"""Concrete implementation of BaseBiometricProvider for Google Health API (Fitbit Air / modern trackers).

Conforms 100% to the official Google Health API v1 specification:
https://health.googleapis.com/v1
"""

import logging
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from ..auth.google_auth import GoogleHealthOAuthClient
from ..auth.tokens import TokenManager
from ..protocol.activities import Activity
from ..protocol.biometrics import DailyPhysiology, HRVData, SleepData
from ..protocol.telemetry import ActivityTelemetry, TelemetryPoint
from ..protocol.user import UserProfile
from .base import BaseBiometricProvider

log = logging.getLogger(__name__)
GOOGLE_HEALTH_API_BASE = "https://health.googleapis.com/v1"


class GoogleHealthProvider(BaseBiometricProvider):
    """Provider for Google Health API devices (e.g. Fitbit Air, Pixel Watch)."""

    def __init__(
        self,
        client_id: str = "default_client",
        token_path: Path | str | None = None,
        tokens: dict[str, Any] | None = None,
        client_secret: str | None = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_client = GoogleHealthOAuthClient(
            client_id=client_id, client_secret=client_secret
        )
        self.token_manager = TokenManager(
            client_id=client_id,
            token_path=token_path,
            initial_tokens=tokens,
            client_secret=client_secret,
        )

    def _get_headers(self) -> dict[str, str]:
        token = self.token_manager.get_valid_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def get_activities(self, start_date: date, end_date: date) -> list[Activity]:
        """Fetches activity sessions from Google Health API."""
        url = f"{GOOGLE_HEALTH_API_BASE}/users/me/activity/sessions"
        params = {
            "startTime": f"{start_date.isoformat()}T00:00:00Z",
            "endTime": f"{end_date.isoformat()}T23:59:59Z",
        }
        try:
            with httpx.Client() as client:
                resp = client.get(url, headers=self._get_headers(), params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    sessions = data.get("sessions", [])
                    activities: list[Activity] = []
                    for s in sessions:
                        start_time_str = s.get("startTime", datetime.now(UTC).isoformat())
                        start_dt = datetime.fromisoformat(start_time_str)
                        duration_sec = float(s.get("durationMillis", 0)) / 1000.0
                        activities.append(
                            Activity(
                                id=str(s.get("id") or s.get("sessionId")),
                                name=s.get("name", "Google Health Session"),
                                type=s.get("activityType", "running").lower(),
                                date=start_dt,
                                duration_sec=duration_sec,
                                distance_m=float(s.get("distanceMeters", 0.0)),
                                avg_hr=float(s.get("averageHeartRateBpm")) if s.get("averageHeartRateBpm") else None,
                                max_hr=float(s.get("maxHeartRateBpm")) if s.get("maxHeartRateBpm") else None,
                                calories=float(s.get("calories", 0.0)),
                                elevation_gain=float(s.get("elevationGainMeters", 0.0)),
                            )
                        )
                    return activities
        except (httpx.HTTPError, KeyError, ValueError, TypeError) as e:
            log.warning(f"Failed to fetch Google Health activities: {e}")
        return []

    def get_telemetry(self, activity_id: str) -> ActivityTelemetry:
        """Fetches high-resolution heart rate series for an activity session."""
        url = f"{GOOGLE_HEALTH_API_BASE}/users/me/heartRate/series/{activity_id}"
        points: list[TelemetryPoint] = []
        try:
            with httpx.Client() as client:
                resp = client.get(url, headers=self._get_headers())
                if resp.status_code == 200:
                    samples = resp.json().get("samples", [])
                    for s in samples:
                        pts_dt = datetime.fromisoformat(s["time"])
                        points.append(
                            TelemetryPoint(
                                timestamp=pts_dt,
                                heart_rate=int(s.get("bpm", 0)),
                                cadence=int(s.get("cadence")) if "cadence" in s else None,
                                speed=float(s.get("speed")) if "speed" in s else None,
                                elevation=float(s.get("elevation")) if "elevation" in s else None,
                            )
                        )
        except (httpx.HTTPError, KeyError, ValueError, TypeError) as e:
            log.warning(f"Failed to fetch Google Health telemetry for session {activity_id}: {e}")

        return ActivityTelemetry(activity_id=activity_id, points=points)

    def get_sleep_history(self, start_date: date, end_date: date) -> list[SleepData]:
        """Fetches sleep sessions from Google Health API."""
        url = f"{GOOGLE_HEALTH_API_BASE}/users/me/sleep/sessions"
        params = {
            "startTime": f"{start_date.isoformat()}T00:00:00Z",
            "endTime": f"{end_date.isoformat()}T23:59:59Z",
        }
        results: list[SleepData] = []
        try:
            with httpx.Client() as client:
                resp = client.get(url, headers=self._get_headers(), params=params)
                if resp.status_code == 200:
                    for s in resp.json().get("sleepSessions", []):
                        sleep_date_str = str(s.get("date", start_date.isoformat()))
                        dur_ms = s.get("durationMillis", 0)
                        stages = s.get("stages", {})
                        results.append(
                            SleepData(
                                date=sleep_date_str,
                                duration_sec=dur_ms // 1000,
                                deep_sec=stages.get("deepMillis", 0) // 1000,
                                light_sec=stages.get("lightMillis", 0) // 1000,
                                rem_sec=stages.get("remMillis", 0) // 1000,
                                awake_sec=stages.get("awakeMillis", 0) // 1000,
                                quality=s.get("efficiencyScore"),
                            )
                        )
        except (httpx.HTTPError, KeyError, ValueError, TypeError) as e:
            log.warning(f"Failed to fetch Google Health sleep: {e}")
        return results

    def get_hrv_history(self, start_date: date, end_date: date) -> list[HRVData]:
        """Fetches daily HRV records."""
        url = f"{GOOGLE_HEALTH_API_BASE}/users/me/dailyMetrics/hrv"
        params = {"startDate": start_date.isoformat(), "endDate": end_date.isoformat()}
        results: list[HRVData] = []
        try:
            with httpx.Client() as client:
                resp = client.get(url, headers=self._get_headers(), params=params)
                if resp.status_code == 200:
                    for item in resp.json().get("hrvMetrics", []):
                        d_str = str(item["date"])
                        results.append(
                            HRVData(
                                date=d_str,
                                last_night_avg=float(item.get("rmssd", 0.0)),
                            )
                        )
        except (httpx.HTTPError, KeyError, ValueError, TypeError) as e:
            log.warning(f"Failed to fetch Google Health HRV: {e}")
        return results

    def get_user_profile(self) -> UserProfile | None:
        """Fetches user identity profile."""
        url = "https://www.googleapis.com/oauth2/v2/userinfo"
        try:
            with httpx.Client() as client:
                resp = client.get(url, headers=self._get_headers())
                if resp.status_code == 200:
                    data = resp.json()
                    return UserProfile(
                        user_id=data.get("id", "google_user"),
                        full_name=data.get("name", "Google Athlete"),
                        gender=data.get("gender"),
                    )
        except (httpx.HTTPError, KeyError, ValueError, TypeError) as e:
            log.warning(f"Failed to fetch Google user profile: {e}")
        return None

    def get_daily_physiology(self, start_date: date, end_date: date) -> list[DailyPhysiology]:
        """Consolidates daily metrics across days."""
        sleep_map = {s.date: s for s in self.get_sleep_history(start_date, end_date)}
        hrv_map = {h.date: h for h in self.get_hrv_history(start_date, end_date)}

        results: list[DailyPhysiology] = []
        curr = start_date
        while curr <= end_date:
            curr_str = curr.isoformat()
            sleep = sleep_map.get(curr_str)
            hrv = hrv_map.get(curr_str)
            results.append(
                DailyPhysiology(
                    date=curr_str,
                    resting_heart_rate=None,
                    hrv_rmssd=hrv.last_night_avg if hrv else None,
                    sleep_score=sleep.quality if sleep else None,
                    sleep_duration_seconds=float(sleep.duration_sec) if sleep and sleep.duration_sec else None,
                    body_battery_max=None,
                    body_battery_min=None,
                    stress_avg=None,
                )
            )
            curr += timedelta(days=1)
        return results
