"""Normalizes Fitbit HRV records into canonical HRVData models."""

from typing import Any

from ..protocol.biometrics import HRVData


def normalize_hrv(raw: dict[str, Any]) -> HRVData:
    """Converts a Fitbit HRV entry to canonical HRVData model."""
    date_str = raw.get("dateTime", "")
    val = raw.get("value", {})

    # dailyRmssd is the standard overnight RMSSD
    daily_rmssd = val.get("dailyRmssd")

    return HRVData(
        date=date_str,
        last_night_avg=float(daily_rmssd) if daily_rmssd is not None else None,
        status="BALANCED" if daily_rmssd and daily_rmssd > 30 else "UNBALANCED",
    )
