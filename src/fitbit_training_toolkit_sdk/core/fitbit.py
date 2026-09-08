"""Concrete implementation of BaseBiometricProvider for Fitbit Web API."""

import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import httpx

from ..auth.tokens import TokenManager
from ..normalizers.activities import normalize_activity
from ..normalizers.hrv import normalize_hrv
from ..normalizers.sleep import normalize_sleep
from ..protocol.activities import Activity
from ..protocol.biometrics import DailyPhysiology, HRVData, SleepData
from ..protocol.telemetry import ActivityTelemetry
from ..protocol.user import UserProfile
from .base import BaseBiometricProvider

log = logging.getLogger(__name__)
FITBIT_API_BASE = "https://api.fitbit.com"


class FitbitProvider(BaseBiometricProvider):
    """Fitbit Web API Biometric Provider."""

    def __init__(
        self,
        client_id: str = "default_client",
        token_path: Path | str | None = None,
        tokens: dict[str, Any] | None = None,
        client_secret: str | None = None,
    ):
        self.token_manager = TokenManager(
            client_id=client_id,
            token_path=token_path,
            initial_tokens=tokens,
            client_secret=client_secret,
        )

    def _headers(self) -> dict[str, str]:
        token = self.token_manager.get_valid_access_token()
        return {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    def get_activities(self, start_date: date, end_date: date) -> list[Activity]:
        url = f"{FITBIT_API_BASE}/1/user/-/activities/list.json"
        params = {
            "afterDate": start_date.isoformat(),
            "sort": "asc",
            "limit": 50,
            "offset": 0,
        }
        resp = httpx.get(url, headers=self._headers(), params=params)
        resp.raise_for_status()
        data = resp.json()
        raw_activities = data.get("activities", [])
        return [normalize_activity(a) for a in raw_activities]

    def get_telemetry(self, activity_id: str) -> ActivityTelemetry:
        # Fitbit TCX or Intraday Heart Rate
        return ActivityTelemetry(activity_id=activity_id, points=[])

    def get_sleep_history(self, start_date: date, end_date: date) -> list[SleepData]:
        url = f"{FITBIT_API_BASE}/1.2/user/-/sleep/date/{start_date.isoformat()}/{end_date.isoformat()}.json"
        resp = httpx.get(url, headers=self._headers())
        resp.raise_for_status()
        data = resp.json()
        raw_sleep = data.get("sleep", [])
        return [normalize_sleep(s) for s in raw_sleep]

    def get_hrv_history(self, start_date: date, end_date: date) -> list[HRVData]:
        url = f"{FITBIT_API_BASE}/1/user/-/hrv/date/{start_date.isoformat()}/{end_date.isoformat()}.json"
        resp = httpx.get(url, headers=self._headers())
        resp.raise_for_status()
        data = resp.json()
        raw_hrv = data.get("hrv", [])
        return [normalize_hrv(h) for h in raw_hrv]

    def get_user_profile(self) -> UserProfile | None:
        url = f"{FITBIT_API_BASE}/1/user/-/profile.json"
        resp = httpx.get(url, headers=self._headers())
        resp.raise_for_status()
        user_raw = resp.json().get("user", {})
        return UserProfile(
            user_id=user_raw.get("encodedId", "fitbit_user"),
            full_name=user_raw.get("fullName"),
            age=user_raw.get("age"),
            gender=user_raw.get("gender"),
            weight_kg=user_raw.get("weight"),
            height_cm=user_raw.get("height"),
        )

    def get_daily_physiology(self, start_date: date, end_date: date) -> list[DailyPhysiology]:
        hrv_list = {h.date: h for h in self.get_hrv_history(start_date, end_date)}
        sleep_list = {s.date: s for s in self.get_sleep_history(start_date, end_date)}

        results = []
        curr = start_date
        while curr <= end_date:
            d_str = curr.isoformat()
            hrv = hrv_list.get(d_str)
            sleep = sleep_list.get(d_str)
            results.append(
                DailyPhysiology(
                    date=d_str,
                    hrv_rmssd=hrv.last_night_avg if hrv else None,
                    sleep_duration_seconds=float(sleep.duration_sec) if sleep and sleep.duration_sec else None,
                    sleep_score=sleep.quality if sleep else None,
                )
            )
            curr += timedelta(days=1)
        return results
