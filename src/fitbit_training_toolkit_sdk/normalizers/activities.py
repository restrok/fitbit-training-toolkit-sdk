"""Normalizes Fitbit activity responses into canonical Activity models."""

from datetime import UTC, datetime
from typing import Any

from ..protocol.activities import Activity, HRZoneTime


def normalize_activity(raw: dict[str, Any]) -> Activity:
    """Converts a Fitbit activity dictionary to canonical Activity model."""
    start_str = raw.get("startTime") or raw.get("originalStartTime") or raw.get("dateTime", "")
    date_val = datetime.fromisoformat(start_str) if start_str else datetime.now(UTC)

    # Duration in milliseconds to seconds
    duration_ms = raw.get("duration", 0)
    duration_sec = duration_ms / 1000.0 if duration_ms else None

    # Distance in kilometers or meters
    distance_raw = raw.get("distance", 0.0)
    # Fitbit distance is typically km for running
    distance_m = distance_raw * 1000.0 if distance_raw else None

    # Heart rate zones
    hr_zones = []
    raw_zones = raw.get("heartRateZones", [])
    for idx, z in enumerate(raw_zones):
        hr_zones.append(
            HRZoneTime(
                zone_number=idx + 1,
                secs_in_zone=float(z.get("minutes", 0) * 60),
                zone_low_boundary_bpm=int(z.get("min", 0)),
            )
        )

    return Activity(
        id=str(raw.get("logId", raw.get("activityId", ""))),
        name=raw.get("activityName", "Fitbit Workout"),
        type=raw.get("activityTypeId", raw.get("name", "workout")).lower(),
        date=date_val,
        duration_sec=duration_sec,
        distance_m=distance_m,
        avg_hr=float(raw["averageHeartRate"]) if "averageHeartRate" in raw else None,
        calories=float(raw["calories"]) if "calories" in raw else None,
        elevation_gain=float(raw["elevationGain"]) if "elevationGain" in raw else None,
        hr_zones=hr_zones,
    )
