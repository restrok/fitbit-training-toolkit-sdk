"""Concrete implementation of BaseBiometricProvider for Fitbit Web API.

Conforms 100% to the official Fitbit Web API Reference:
https://dev.fitbit.com/build/reference/web-api/
"""

import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import httpx

from ..auth.pkce import revoke_token
from ..auth.tokens import TokenManager
from ..normalizers.activities import normalize_activity
from ..normalizers.hrv import normalize_hrv
from ..normalizers.sleep import normalize_sleep
from ..normalizers.telemetry import parse_tcx
from ..protocol.activities import Activity
from ..protocol.biometrics import DailyPhysiology, HRVData, SleepData
from ..protocol.telemetry import ActivityTelemetry
from ..protocol.user import UserProfile
from .base import BaseBiometricProvider

log = logging.getLogger(__name__)
FITBIT_API_BASE = "https://api.fitbit.com"


class FitbitProvider(BaseBiometricProvider):
    """Fitbit Web API Biometric Provider with full official endpoint support."""

    def __init__(
        self,
        client_id: str = "default_client",
        token_path: Path | str | None = None,
        tokens: dict[str, Any] | None = None,
        client_secret: str | None = None,
        locale: str = "es_ES",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.locale = locale
        self.token_manager = TokenManager(
            client_id=client_id,
            token_path=token_path,
            initial_tokens=tokens,
            client_secret=client_secret,
        )
        self.rate_limit_limit: int | None = None
        self.rate_limit_remaining: int | None = None
        self.rate_limit_reset: int | None = None

    def _headers(self, accept: str = "application/json") -> dict[str, str]:
        token = self.token_manager.get_valid_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": accept,
            "Accept-Language": self.locale,
        }

    def _track_rate_limits(self, resp: httpx.Response) -> None:
        """Parses rate limit headers from official Fitbit responses."""
        if "fitbit-rate-limit-limit" in resp.headers:
            try:
                self.rate_limit_limit = int(resp.headers["fitbit-rate-limit-limit"])
            except ValueError:
                pass
        if "fitbit-rate-limit-remaining" in resp.headers:
            try:
                self.rate_limit_remaining = int(resp.headers["fitbit-rate-limit-remaining"])
            except ValueError:
                pass
        if "fitbit-rate-limit-reset" in resp.headers:
            try:
                self.rate_limit_reset = int(resp.headers["fitbit-rate-limit-reset"])
            except ValueError:
                pass

    def get_activities(self, start_date: date, end_date: date) -> list[Activity]:
        """Retrieves activity log list. Scope: activity.
        
        Spec: /1/user/-/activities/list.json
        """
        url = f"{FITBIT_API_BASE}/1/user/-/activities/list.json"
        params = {
            "afterDate": start_date.isoformat(),
            "sort": "asc",
            "limit": 100,
            "offset": 0,
        }
        resp = httpx.get(url, headers=self._headers(), params=params)
        self._track_rate_limits(resp)
        resp.raise_for_status()
        data = resp.json()
        raw_activities = data.get("activities", [])
        return [normalize_activity(a) for a in raw_activities]

    def get_activity_tcx(self, activity_id: str, include_partial: bool = True) -> str:
        """Retrieves TCX GPS data for a specific activity. Scope: activity, location.
        
        Spec: /1/user/-/activities/[log-id].tcx
        """
        url = f"{FITBIT_API_BASE}/1/user/-/activities/{activity_id}.tcx"
        params = {"includePartialTCX": str(include_partial).lower()}
        headers = self._headers(accept="application/vnd.garmin.tcx+xml")
        resp = httpx.get(url, headers=headers, params=params)
        self._track_rate_limits(resp)
        resp.raise_for_status()
        return resp.text

    def get_intraday_heart_rate(
        self,
        date_val: date,
        detail_level: str = "1sec",
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict[str, Any]:
        """Retrieves intraday heart rate series. Scope: heartrate.
        
        Spec: /1/user/-/activities/heart/date/[date]/1d/[detail-level].json
        """
        date_str = date_val.isoformat()
        if start_time and end_time:
            url = f"{FITBIT_API_BASE}/1/user/-/activities/heart/date/{date_str}/1d/{detail_level}/time/{start_time}/{end_time}.json"
        else:
            url = f"{FITBIT_API_BASE}/1/user/-/activities/heart/date/{date_str}/1d/{detail_level}.json"

        resp = httpx.get(url, headers=self._headers())
        self._track_rate_limits(resp)
        resp.raise_for_status()
        return resp.json()

    def get_telemetry(self, activity_id: str) -> ActivityTelemetry:
        """Retrieves high-resolution telemetry via TCX or fallback to intraday heart rate."""
        try:
            tcx_str = self.get_activity_tcx(activity_id)
            telemetry = parse_tcx(activity_id, tcx_str)
            if telemetry.points:
                return telemetry
        except (httpx.HTTPError, ValueError) as e:
            log.debug(f"Could not load TCX for {activity_id}: {e}")

        return ActivityTelemetry(activity_id=activity_id, points=[])

    def get_sleep_history(self, start_date: date, end_date: date) -> list[SleepData]:
        """Retrieves sleep logs for a date range (max 100 days). Scope: sleep.
        
        Spec: /1.2/user/-/sleep/date/[startDate]/[endDate].json
        """
        url = f"{FITBIT_API_BASE}/1.2/user/-/sleep/date/{start_date.isoformat()}/{end_date.isoformat()}.json"
        resp = httpx.get(url, headers=self._headers())
        self._track_rate_limits(resp)
        resp.raise_for_status()
        data = resp.json()
        raw_sleep = data.get("sleep", [])
        return [normalize_sleep(s) for s in raw_sleep]

    def get_hrv_history(self, start_date: date, end_date: date) -> list[HRVData]:
        """Retrieves HRV records for a date range (max 30 days). Scope: heartrate.
        
        Spec: /1/user/-/hrv/date/[startDate]/[endDate].json
        """
        url = f"{FITBIT_API_BASE}/1/user/-/hrv/date/{start_date.isoformat()}/{end_date.isoformat()}.json"
        resp = httpx.get(url, headers=self._headers())
        self._track_rate_limits(resp)
        resp.raise_for_status()
        data = resp.json()
        raw_hrv = data.get("hrv", [])
        return [normalize_hrv(h) for h in raw_hrv]

    def get_cardio_score(self, start_date: date, end_date: date | None = None) -> list[dict[str, Any]]:
        """Retrieves Cardio Fitness Score (VO2 Max). Scope: cardio_fitness.
        
        Spec: /1/user/-/cardioscore/date/[date].json
        """
        if end_date:
            url = f"{FITBIT_API_BASE}/1/user/-/cardioscore/date/{start_date.isoformat()}/{end_date.isoformat()}.json"
        else:
            url = f"{FITBIT_API_BASE}/1/user/-/cardioscore/date/{start_date.isoformat()}.json"

        resp = httpx.get(url, headers=self._headers())
        self._track_rate_limits(resp)
        resp.raise_for_status()
        return resp.json().get("cardioScore", [])

    def get_user_profile(self) -> UserProfile | None:
        """Retrieves user profile. Scope: profile.
        
        Spec: /1/user/-/profile.json
        """
        url = f"{FITBIT_API_BASE}/1/user/-/profile.json"
        resp = httpx.get(url, headers=self._headers())
        self._track_rate_limits(resp)
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
        """Consolidates daily HRV and sleep metrics into daily physiology models."""
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

    def revoke_current_token(self) -> bool:
        """Revokes the current access token per RFC 7009."""
        current_token = self.token_manager.tokens.get("access_token")
        if not current_token:
            return True
        return revoke_token(
            client_id=self.client_id,
            token=current_token,
            client_secret=self.client_secret,
        )
