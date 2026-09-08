from datetime import date

from fitbit_training_toolkit_sdk.testing.mock import MockFitbitProvider


def test_mock_provider():
    provider = MockFitbitProvider()
    acts = provider.get_activities(date(2026, 9, 1), date(2026, 9, 8))
    assert len(acts) == 1
    assert acts[0].name == "Morning Treadmill Run"

    sleep = provider.get_sleep_history(date(2026, 9, 1), date(2026, 9, 8))
    assert len(sleep) == 1
    assert sleep[0].quality == 86

    hrv = provider.get_hrv_history(date(2026, 9, 1), date(2026, 9, 8))
    assert len(hrv) == 1
    assert hrv[0].last_night_avg == 64.5

    physio = provider.get_daily_physiology(date(2026, 9, 8), date(2026, 9, 8))
    assert len(physio) == 1
    assert physio[0].resting_heart_rate == 48
