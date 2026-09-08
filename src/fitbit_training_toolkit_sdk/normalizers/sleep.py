"""Normalizes Fitbit sleep records into canonical SleepData models.

Specification: https://dev.fitbit.com/build/reference/web-api/sleep/get-sleep-log-by-date-range/
Supports both 'stages' (30-sec epochs) and 'classic' (1-min epochs) sleep logs.
"""

from typing import Any

from ..protocol.biometrics import SleepData


def normalize_sleep(raw: dict[str, Any]) -> SleepData:
    """Converts a Fitbit sleep record to canonical SleepData model.

    Handles official types:
      - 'stages': levels.summary contains 'deep', 'light', 'rem', 'wake'
      - 'classic': levels.summary contains 'asleep', 'awake', 'restless'
    """
    date_str = raw.get("dateOfSleep", "")
    duration_ms = raw.get("duration", 0)
    duration_sec = duration_ms // 1000 if duration_ms else 0

    log_type = raw.get("type", "stages")
    levels = raw.get("levels", {})
    summary = levels.get("summary", {})

    if log_type == "classic":
        asleep_min = summary.get("asleep", {}).get("minutes", raw.get("minutesAsleep", 0))
        awake_min = summary.get("awake", {}).get("minutes", raw.get("minutesAwake", 0))
        restless_min = summary.get("restless", {}).get("minutes", 0)

        deep_sec = 0
        light_sec = asleep_min * 60
        rem_sec = 0
        awake_sec = (awake_min + restless_min) * 60
    else:
        # Default 'stages' log
        deep_min = summary.get("deep", {}).get("minutes", 0)
        light_min = summary.get("light", {}).get("minutes", 0)
        rem_min = summary.get("rem", {}).get("minutes", 0)
        wake_min = summary.get("wake", {}).get("minutes", raw.get("minutesAwake", 0))

        deep_sec = deep_min * 60
        light_sec = light_min * 60
        rem_sec = rem_min * 60
        awake_sec = wake_min * 60

    # Efficiency calculation (Fitbit efficiency is 0-100 score)
    quality = raw.get("efficiency")
    if quality is None and raw.get("timeInBed") and raw.get("minutesAsleep"):
        quality = int((raw["minutesAsleep"] / raw["timeInBed"]) * 100)

    return SleepData(
        date=date_str,
        duration_sec=duration_sec,
        deep_sec=deep_sec,
        light_sec=light_sec,
        rem_sec=rem_sec,
        awake_sec=awake_sec,
        quality=quality,
    )
