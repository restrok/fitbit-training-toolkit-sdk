"""Mock provider for testing without live Fitbit credentials.

Returns deterministic data structured according to official Fitbit API schemas.
"""

from datetime import UTC, date, datetime
from typing import Any

from ..core.base import BaseBiometricProvider
from ..protocol.activities import Activity, HRZoneTime
from ..protocol.biometrics import DailyPhysiology, HRVData, SleepData
from ..protocol.telemetry import ActivityTelemetry, TelemetryPoint
from ..protocol.user import UserProfile


class MockFitbitProvider(BaseBiometricProvider):
    """Returns deterministic synthetic data for unit tests and local simulations."""

    def get_activities(self, start_date: date, end_date: date) -> list[Activity]:
        return [
            Activity(
                id="fb_act_9001",
                name="Morning Treadmill Run",
                type="running",
                date=datetime(2026, 9, 8, 7, 30, 0, tzinfo=UTC),
                duration_sec=2700.0,
                distance_m=6000.0,
                avg_hr=148.0,
                calories=420.0,
                hr_zones=[
                    HRZoneTime(zone_number=1, secs_in_zone=300.0, zone_low_boundary_bpm=110),
                    HRZoneTime(zone_number=2, secs_in_zone=1800.0, zone_low_boundary_bpm=135),
                    HRZoneTime(zone_number=3, secs_in_zone=600.0, zone_low_boundary_bpm=155),
                ],
            )
        ]

    def get_telemetry(self, activity_id: str) -> ActivityTelemetry:
        return ActivityTelemetry(
            activity_id=activity_id,
            points=[
                TelemetryPoint(timestamp=datetime(2026, 9, 8, 7, 30, 0, tzinfo=UTC), heart_rate=135, elevation=25.0),
                TelemetryPoint(timestamp=datetime(2026, 9, 8, 7, 31, 0, tzinfo=UTC), heart_rate=145, elevation=26.0),
            ],
        )

    def get_sleep_history(self, start_date: date, end_date: date) -> list[SleepData]:
        return [
            SleepData(
                date="2026-09-08",
                duration_sec=28800,
                deep_sec=5400,
                light_sec=14400,
                rem_sec=7200,
                awake_sec=1800,
                quality=86,
            )
        ]

    def get_hrv_history(self, start_date: date, end_date: date) -> list[HRVData]:
        return [
            HRVData(
                date="2026-09-08",
                last_night_avg=64.5,
                status="BALANCED",
            )
        ]

    def get_cardio_score(self, start_date: date, end_date: date | None = None) -> list[dict[str, Any]]:
        return [
            {
                "dateTime": "2026-09-08",
                "value": {"vo2Max": "48"},
            }
        ]

    def get_user_profile(self) -> UserProfile | None:
        return UserProfile(
            user_id="fb_user_1",
            full_name="Athlete Test",
            age=35,
            weight_kg=72.5,
            height_cm=178.0,
        )

    def get_daily_physiology(self, start_date: date, end_date: date) -> list[DailyPhysiology]:
        return [
            DailyPhysiology(
                date="2026-09-08",
                resting_heart_rate=48,
                hrv_rmssd=64.5,
                body_battery_max=92,
                body_battery_min=24,
                sleep_duration_seconds=28800.0,
                sleep_score=86,
            )
        ]
