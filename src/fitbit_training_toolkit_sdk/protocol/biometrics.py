
from pydantic import BaseModel


class HRVData(BaseModel):
    date: str
    last_night_avg: float | None = None
    min_hrv: float | None = None
    max_hrv: float | None = None
    status: str | None = None
    baseline_low: float | None = None
    baseline_high: float | None = None


class SleepData(BaseModel):
    date: str
    start: int | None = None
    end: int | None = None
    duration_sec: int | None = None
    deep_sec: int | None = None
    light_sec: int | None = None
    rem_sec: int | None = None
    awake_sec: int | None = None
    quality: int | None = None


class DailyPhysiology(BaseModel):
    date: str
    resting_heart_rate: int | None = None
    hrv_rmssd: float | None = None
    body_battery_max: int | None = None
    body_battery_min: int | None = None
    stress_avg: int | None = None
    sleep_duration_seconds: float | None = None
    sleep_score: int | None = None
