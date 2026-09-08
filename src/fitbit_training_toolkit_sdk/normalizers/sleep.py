"""Normalizes Fitbit sleep records into canonical SleepData models."""

from typing import Any

from ..protocol.biometrics import SleepData


def normalize_sleep(raw: dict[str, Any]) -> SleepData:
    """Converts a Fitbit sleep record to canonical SleepData model."""
    date_str = raw.get("dateOfSleep", "")
    duration_ms = raw.get("duration", 0)
    duration_sec = duration_ms // 1000

    levels = raw.get("levels", {})
    summary = levels.get("summary", {})

    deep_min = summary.get("deep", {}).get("minutes", 0)
    light_min = summary.get("light", {}).get("minutes", 0)
    rem_min = summary.get("rem", {}).get("minutes", 0)
    wake_min = summary.get("wake", {}).get("minutes", 0)

    quality = raw.get("efficiency")

    return SleepData(
        date=date_str,
        duration_sec=duration_sec,
        deep_sec=deep_min * 60,
        light_sec=light_min * 60,
        rem_sec=rem_min * 60,
        awake_sec=wake_min * 60,
        quality=quality,
    )
