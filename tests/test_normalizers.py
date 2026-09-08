from fitbit_training_toolkit_sdk.normalizers.activities import normalize_activity
from fitbit_training_toolkit_sdk.normalizers.hrv import normalize_hrv
from fitbit_training_toolkit_sdk.normalizers.sleep import normalize_sleep


def test_normalize_activity():
    raw = {
        "logId": 123456,
        "activityName": "Outdoor Run",
        "name": "Run",
        "startTime": "2026-09-08T08:00:00Z",
        "duration": 1800000,  # 30 min in ms
        "distance": 5.0,     # 5 km
        "averageHeartRate": 150,
        "calories": 350,
        "heartRateZones": [
            {"minutes": 10, "min": 120},
            {"minutes": 20, "min": 145}
        ]
    }
    act = normalize_activity(raw)
    assert act.id == "123456"
    assert act.name == "Outdoor Run"
    assert act.duration_sec == 1800.0
    assert act.distance_m == 5000.0
    assert act.avg_hr == 150.0
    assert len(act.hr_zones) == 2


def test_normalize_sleep():
    raw = {
        "dateOfSleep": "2026-09-08",
        "duration": 28800000,
        "efficiency": 90,
        "levels": {
            "summary": {
                "deep": {"minutes": 90},
                "light": {"minutes": 240},
                "rem": {"minutes": 120},
                "wake": {"minutes": 30}
            }
        }
    }
    s = normalize_sleep(raw)
    assert s.date == "2026-09-08"
    assert s.duration_sec == 28800
    assert s.deep_sec == 5400
    assert s.quality == 90


def test_normalize_hrv():
    raw = {
        "dateTime": "2026-09-08",
        "value": {
            "dailyRmssd": 58.2
        }
    }
    h = normalize_hrv(raw)
    assert h.date == "2026-09-08"
    assert h.last_night_avg == 58.2
    assert h.status == "BALANCED"
