from datetime import datetime

from pydantic import BaseModel, Field


class TelemetryPoint(BaseModel):
    timestamp: datetime
    heart_rate: int | None = None
    cadence: int | None = None
    speed: float | None = None
    elevation: float | None = None


class ActivityTelemetry(BaseModel):
    activity_id: str
    points: list[TelemetryPoint] = Field(default_factory=list)
