import os
import sys
from collections.abc import Mapping
from datetime import date

import pytest
from dotenv import load_dotenv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from api.app.services.context_aggregator import (
    ContextAggregator,
    WeatherFetchError,
)

load_dotenv()


class _DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


def test_get_todays_weather_forecast(monkeypatch):
    """Ensure weather forecast aggregates expected fields."""

    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "fake-key")
    monkeypatch.setenv("EDINBURGH_FESTIVALS_DEFAULT_FESTIVAL", "")

    def fake_get(url, params, **kwargs):
        if "geo" in url:
            return _DummyResponse([{"lat": 55.9533, "lon": -3.1883}])
        return _DummyResponse(
            {
                "main": {"temp": 12.3, "feels_like": 11.0, "humidity": 87},
                "wind": {"speed": 3.6},
                "clouds": {"all": 75},
                "rain": {"1h": 0.2},
                "snow": None,
            }
        )

    monkeypatch.setattr(
        "api.app.services.context_aggregator.requests.get", fake_get
    )

    aggregator = ContextAggregator()
    forecast = aggregator.get_todays_weather_forecast(
        "Edinburgh", "GB", date(2025, 1, 1)
    )

    assert isinstance(forecast, Mapping)
    assert forecast["date"] == "2025-01-01"
    assert forecast["temperature"] == 12.3
    assert forecast["feels_like"] == 11.0
    assert forecast["humidity"] == 87
    assert forecast["wind_speed"] == 3.6
    assert forecast["percent_cloudiness"] == 75
    assert forecast["rain_mm_per_h"] == {"1h": 0.2}
    assert forecast["snow_mm_per_h"] is None


def test_gather_context_includes_defaults(monkeypatch):
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "fake-key")

    def fake_get(url, params, **kwargs):
        return (
            _DummyResponse([{"lat": 55.9533, "lon": -3.1883}])
            if "geo" in url
            else _DummyResponse(
                {
                    "main": {"temp": 10.0, "feels_like": 9.0, "humidity": 80},
                    "wind": {"speed": 5.0},
                    "clouds": {"all": 60},
                }
            )
        )

    monkeypatch.setattr(
        "api.app.services.context_aggregator.requests.get", fake_get
    )
    monkeypatch.setattr(
        "api.app.services.context_aggregator.fetch_festival_events",
        lambda target_date, **kwargs: {"date": target_date.isoformat(), "events": []},
    )

    aggregator = ContextAggregator()
    context = aggregator.gather_context("Music events")

    assert context["preferences"] == "music events"
    assert context["city"] == "Edinburgh"
    assert isinstance(context["weather"], Mapping)
    assert context["weather_error"] is None
    assert context["festival_events"]["date"] == context["date"]
    assert context["festival_events"]["events"] == []


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("OPENWEATHERMAP_API_KEY"),
    reason="LIVE test requires OPENWEATHERMAP_API_KEY",
)
def test_gather_context_live_weather():
    """Smoke-test the live OpenWeatherMap integration when credentials are present."""
    aggregator = ContextAggregator()
    try:
        weather = aggregator.get_todays_weather_forecast(
            "Edinburgh", "GB", date.today()
        )
    except WeatherFetchError as exc:
        message = str(exc).lower()
        if "invalid api key" in message or "401" in message:
            pytest.skip(f"OpenWeatherMap rejected API key: {exc}")
        raise

    for field in ("temperature", "feels_like", "humidity", "wind_speed"):
        assert field in weather, f"Missing `{field}` in live weather payload"
