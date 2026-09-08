"""Normalizes Fitbit HRV records into canonical HRVData models.

Specification: https://dev.fitbit.com/build/reference/web-api/heartrate-variability/get-hrv-summary-by-interval/
"""

from typing import Any

from ..protocol.biometrics import HRVData


def normalize_hrv(raw: dict[str, Any]) -> HRVData:
    """Converts a Fitbit HRV entry to canonical HRVData model.

    Fitbit returns:
      - dateTime: 'YYYY-MM-DD'
      - value.dailyRmssd: overnight RMSSD in milliseconds
      - value.deepRmssd: RMSSD during deep sleep in milliseconds
    """
    date_str = raw.get("dateTime", "")
    val = raw.get("value", {})

    daily_rmssd = val.get("dailyRmssd")
    deep_rmssd = val.get("deepRmssd")

    score = daily_rmssd if daily_rmssd is not None else deep_rmssd

    return HRVData(
        date=date_str,
        last_night_avg=float(score) if score is not None else None,
        status="BALANCED" if score and float(score) >= 30.0 else "UNBALANCED",
    )
