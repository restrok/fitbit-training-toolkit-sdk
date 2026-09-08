"""Normalizes Fitbit activity responses into canonical Activity models.

Specification: https://dev.fitbit.com/build/reference/web-api/activity/get-activity-log-list/
"""

from datetime import UTC, datetime
from typing import Any

from ..protocol.activities import Activity, HRZoneTime

# Mapping official Fitbit heartRateZone names to canonical numbers
ZONE_NAME_MAP = {
    "out of range": 1,
    "below": 1,
    "out_of_zone": 1,
    "fat burn": 2,
    "fat_burn": 2,
    "cardio": 3,
    "peak": 4,
    "above": 4,
}


def normalize_activity(raw: dict[str, Any]) -> Activity:
    """Converts a Fitbit activity dictionary to canonical Activity model.

    Handles official fields:
      - logId: unique integer/string activity identifier
      - activityName / name / activityTypeId
      - duration / activeDuration in milliseconds -> seconds
      - distance (km in metric unit system) -> meters
      - heartRateZones: list of zones with official names ('Out of Range', 'Fat Burn', 'Cardio', 'Peak')
      - calories, elevationGain, averageHeartRate
    """
    start_str = raw.get("startTime") or raw.get("originalStartTime") or raw.get("dateTime", "")
    date_val = datetime.fromisoformat(start_str) if start_str else datetime.now(UTC)

    # Duration: Fitbit returns milliseconds
    duration_ms = raw.get("duration") or raw.get("activeDuration") or 0
    duration_sec = float(duration_ms) / 1000.0 if duration_ms else None

    # Distance: Fitbit returns float (km if metric Accept-Language is passed)
    distance_raw = raw.get("distance")
    distance_m = float(distance_raw) * 1000.0 if distance_raw is not None else None

    # Heart rate zones
    hr_zones: list[HRZoneTime] = []
    raw_zones = raw.get("heartRateZones", [])
    for idx, z in enumerate(raw_zones):
        z_name = str(z.get("name", "")).lower()
        zone_num = ZONE_NAME_MAP.get(z_name, idx + 1)
        minutes = z.get("minutes", 0)
        min_bpm = z.get("min", 0)
        hr_zones.append(
            HRZoneTime(
                zone_number=zone_num,
                secs_in_zone=float(minutes * 60),
                zone_low_boundary_bpm=int(min_bpm),
            )
        )

    # Activity name & type safe resolution
    act_name = raw.get("activityName") or raw.get("name") or "Fitbit Workout"
    raw_type = raw.get("activityName") or raw.get("activityTypeId") or "workout"
    act_type = str(raw_type).lower()

    return Activity(
        id=str(raw.get("logId", raw.get("activityId", ""))),
        name=act_name,
        type=act_type,
        date=date_val,
        duration_sec=duration_sec,
        distance_m=distance_m,
        avg_hr=float(raw["averageHeartRate"]) if "averageHeartRate" in raw and raw["averageHeartRate"] is not None else None,
        calories=float(raw["calories"]) if "calories" in raw and raw["calories"] is not None else None,
        elevation_gain=float(raw["elevationGain"]) if "elevationGain" in raw and raw["elevationGain"] is not None else None,
        hr_zones=hr_zones,
    )
