from datetime import date

from fitbit_training_toolkit_sdk.testing.mock import MockFitbitProvider


def test_mock_provider_official_suite():
    provider = MockFitbitProvider()
    acts = provider.get_activities(date(2026, 9, 1), date(2026, 9, 8))
    assert len(acts) == 1
    assert acts[0].name == "Morning Treadmill Run"
    assert acts[0].distance_m == 6000.0

    sleep = provider.get_sleep_history(date(2026, 9, 1), date(2026, 9, 8))
    assert len(sleep) == 1
    assert sleep[0].quality == 86

    hrv = provider.get_hrv_history(date(2026, 9, 1), date(2026, 9, 8))
    assert len(hrv) == 1
    assert hrv[0].last_night_avg == 64.5

    vo2 = provider.get_cardio_score(date(2026, 9, 8))
    assert len(vo2) == 1
    assert vo2[0]["value"]["vo2Max"] == "48"

    physio = provider.get_daily_physiology(date(2026, 9, 8), date(2026, 9, 8))
    assert len(physio) == 1
    assert physio[0].resting_heart_rate == 48

    tel = provider.get_telemetry("fb_act_9001")
    assert len(tel.points) == 2
    assert tel.points[0].heart_rate == 135
