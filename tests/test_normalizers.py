from fitbit_training_toolkit_sdk.normalizers.activities import normalize_activity
from fitbit_training_toolkit_sdk.normalizers.hrv import normalize_hrv
from fitbit_training_toolkit_sdk.normalizers.sleep import normalize_sleep
from fitbit_training_toolkit_sdk.normalizers.telemetry import (
    parse_intraday_heart_rate,
    parse_tcx,
)


def test_normalize_activity_official_schema():
    raw = {
        "logId": 19018673358,
        "activityName": "Outdoor Run",
        "activityTypeId": 90013,
        "startTime": "2026-09-08T08:00:00.000-03:00",
        "duration": 1800000,
        "distance": 5.2,
        "averageHeartRate": 152,
        "calories": 380,
        "elevationGain": 45.0,
        "heartRateZones": [
            {"name": "Out of Range", "min": 30, "max": 90, "minutes": 5, "caloriesOut": 25.0},
            {"name": "Fat Burn", "min": 91, "max": 125, "minutes": 10, "caloriesOut": 90.0},
            {"name": "Cardio", "min": 126, "max": 160, "minutes": 12, "caloriesOut": 190.0},
            {"name": "Peak", "min": 161, "max": 190, "minutes": 3, "caloriesOut": 75.0},
        ],
    }
    act = normalize_activity(raw)
    assert act.id == "19018673358"
    assert act.name == "Outdoor Run"
    assert act.type == "outdoor run"
    assert act.duration_sec == 1800.0
    assert act.distance_m == 5200.0
    assert act.avg_hr == 152.0
    assert act.elevation_gain == 45.0
    assert len(act.hr_zones) == 4
    assert act.hr_zones[1].zone_number == 2
    assert act.hr_zones[1].secs_in_zone == 600.0


def test_normalize_sleep_stages():
    raw = {
        "dateOfSleep": "2026-09-08",
        "duration": 28800000,
        "efficiency": 92,
        "type": "stages",
        "levels": {
            "summary": {
                "deep": {"minutes": 90},
                "light": {"minutes": 240},
                "rem": {"minutes": 110},
                "wake": {"minutes": 40},
            }
        },
    }
    s = normalize_sleep(raw)
    assert s.date == "2026-09-08"
    assert s.duration_sec == 28800
    assert s.deep_sec == 5400
    assert s.light_sec == 14400
    assert s.rem_sec == 6600
    assert s.awake_sec == 2400
    assert s.quality == 92


def test_normalize_sleep_classic():
    raw = {
        "dateOfSleep": "2026-09-07",
        "duration": 21600000,
        "type": "classic",
        "timeInBed": 360,
        "minutesAsleep": 320,
        "levels": {
            "summary": {
                "asleep": {"minutes": 320},
                "awake": {"minutes": 20},
                "restless": {"minutes": 20},
            }
        },
    }
    s = normalize_sleep(raw)
    assert s.date == "2026-09-07"
    assert s.duration_sec == 21600
    assert s.deep_sec == 0
    assert s.light_sec == 320 * 60
    assert s.awake_sec == 40 * 60
    assert s.quality == 88  # 320 / 360 * 100


def test_normalize_hrv():
    raw = {
        "dateTime": "2026-09-08",
        "value": {
            "dailyRmssd": 62.887,
            "deepRmssd": 64.887,
        },
    }
    h = normalize_hrv(raw)
    assert h.date == "2026-09-08"
    assert h.last_night_avg == 62.887
    assert h.status == "BALANCED"


def test_parse_tcx_and_intraday():
    sample_tcx = """<?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">
  <Activities>
    <Activity Sport="Running">
      <Id>2026-09-08T08:00:00Z</Id>
      <Lap StartTime="2026-09-08T08:00:00Z">
        <Track>
          <Trackpoint>
            <Time>2026-09-08T08:00:01Z</Time>
            <AltitudeMeters>35.0</AltitudeMeters>
            <HeartRateBpm><Value>140</Value></HeartRateBpm>
          </Trackpoint>
          <Trackpoint>
            <Time>2026-09-08T08:00:02Z</Time>
            <AltitudeMeters>35.2</AltitudeMeters>
            <HeartRateBpm><Value>142</Value></HeartRateBpm>
          </Trackpoint>
        </Track>
      </Lap>
    </Activity>
  </Activities>
</TrainingCenterDatabase>"""
    tel = parse_tcx("act_1", sample_tcx)
    assert tel.activity_id == "act_1"
    assert len(tel.points) == 2
    assert tel.points[0].heart_rate == 140
    assert tel.points[0].elevation == 35.0

    sample_intraday = {
        "activities-heart-intraday": {
            "dataset": [
                {"time": "08:00:00", "value": 138},
                {"time": "08:01:00", "value": 142},
            ]
        }
    }
    tel_hr = parse_intraday_heart_rate("act_2", "2026-09-08", sample_intraday)
    assert len(tel_hr.points) == 2
    assert tel_hr.points[1].heart_rate == 142
