"""Normalizes TCX XML and Intraday Heart Rate data into ActivityTelemetry.

Specifications:
  - TCX GPS: https://dev.fitbit.com/build/reference/web-api/activity/get-activity-tcx/
  - Intraday HR: https://dev.fitbit.com/build/reference/web-api/intraday/get-heartrate-intraday-by-date/
"""

import logging
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any

from ..protocol.telemetry import ActivityTelemetry, TelemetryPoint

log = logging.getLogger(__name__)


def parse_tcx(activity_id: str, tcx_content: str) -> ActivityTelemetry:
    """Parses a Garmin Training Center XML (TCX) string into ActivityTelemetry."""
    points: list[TelemetryPoint] = []
    try:
        root = ET.fromstring(tcx_content)
        ns = {"tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}
        for tp in root.findall(".//tcx:Trackpoint", ns):
            time_elem = tp.find("tcx:Time", ns)
            if time_elem is None or not time_elem.text:
                continue

            dt = datetime.fromisoformat(time_elem.text)

            hr_elem = tp.find(".//tcx:HeartRateBpm/tcx:Value", ns)
            hr = int(hr_elem.text) if hr_elem is not None and hr_elem.text else None

            alt_elem = tp.find("tcx:AltitudeMeters", ns)
            alt = float(alt_elem.text) if alt_elem is not None and alt_elem.text else None

            points.append(
                TelemetryPoint(
                    timestamp=dt,
                    heart_rate=hr,
                    elevation=alt,
                )
            )
    except (ET.ParseError, ValueError, KeyError) as e:
        log.warning(f"Failed to parse TCX for {activity_id}: {e}")

    return ActivityTelemetry(activity_id=activity_id, points=points)


def parse_intraday_heart_rate(
    activity_id: str,
    date_str: str,
    intraday_data: dict[str, Any],
) -> ActivityTelemetry:
    """Converts a Fitbit intraday heart rate dataset into ActivityTelemetry."""
    points: list[TelemetryPoint] = []
    dataset = intraday_data.get("activities-heart-intraday", {}).get("dataset", [])

    for entry in dataset:
        time_str = entry.get("time")
        val = entry.get("value")
        if not time_str or val is None:
            continue

        try:
            dt = datetime.fromisoformat(f"{date_str}T{time_str}").replace(tzinfo=UTC)
            points.append(
                TelemetryPoint(
                    timestamp=dt,
                    heart_rate=int(val),
                )
            )
        except (ValueError, KeyError) as e:
            log.debug(f"Skipping malformed intraday entry: {e}")

    return ActivityTelemetry(activity_id=activity_id, points=points)
