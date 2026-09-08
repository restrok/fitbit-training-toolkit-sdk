from abc import ABC, abstractmethod
from datetime import date

from ..protocol.activities import Activity
from ..protocol.biometrics import DailyPhysiology, HRVData, SleepData
from ..protocol.telemetry import ActivityTelemetry
from ..protocol.user import UserProfile


class BaseBiometricProvider(ABC):
    """Abstract base interface for wearable biometric providers."""

    @abstractmethod
    def get_activities(self, start_date: date, end_date: date) -> list[Activity]:
        """Fetches activities within date range."""

    @abstractmethod
    def get_telemetry(self, activity_id: str) -> ActivityTelemetry:
        """Fetches high-resolution telemetry for an activity."""

    @abstractmethod
    def get_sleep_history(self, start_date: date, end_date: date) -> list[SleepData]:
        """Fetches sleep history."""

    @abstractmethod
    def get_hrv_history(self, start_date: date, end_date: date) -> list[HRVData]:
        """Fetches HRV history."""

    @abstractmethod
    def get_user_profile(self) -> UserProfile | None:
        """Fetches user profile."""

    @abstractmethod
    def get_daily_physiology(self, start_date: date, end_date: date) -> list[DailyPhysiology]:
        """Fetches consolidated daily physiology (RHR, HRV, sleep, stress)."""
