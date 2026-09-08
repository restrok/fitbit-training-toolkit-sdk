from datetime import datetime

from pydantic import BaseModel, Field


class HRZoneTime(BaseModel):
    zone_number: int
    secs_in_zone: float
    zone_low_boundary_bpm: int


class ActivitySplit(BaseModel):
    index: int
    distance_m: float | None = None
    duration_sec: float | None = None
    avg_hr: float | None = None
    max_hr: float | None = None
    avg_pace_mps: float | None = None


class Activity(BaseModel):
    id: str
    name: str
    type: str
    date: datetime
    duration_sec: float | None = None
    distance_m: float | None = None
    avg_hr: float | None = None
    max_hr: float | None = None
    calories: float | None = None
    elevation_gain: float | None = None
    hr_zones: list[HRZoneTime] = Field(default_factory=list)
    splits: list[ActivitySplit] = Field(default_factory=list)
