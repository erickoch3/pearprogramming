import os
import sys
from datetime import date
from urllib.parse import parse_qs, urlparse

import pytest
from dotenv import load_dotenv

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../api"))
)

from app.services.scrapers import festivals_api

load_dotenv()


def test_build_signed_path_matches_reference():
    secret = "135fa25acs33"
    params = [("filter", "that"), ("key", "12345678")]

    signed_path = festivals_api._build_signed_path(secret, "/events", params)

    assert (
        signed_path
        == "/events?filter=that&key=12345678&signature=e471178c45d33d7a37f99f74f8ff59d97749e7bf"
    )


def test_fetch_festival_events_maps_payload(monkeypatch):
    monkeypatch.setenv("EDINBURGH_FESTIVALS_API_KEY", "abc123")
    monkeypatch.setenv("EDINBURGH_FESTIVALS_SECRET_KEY", "secret")
    event_date = date(2025, 8, 20)

    payload = [
        {
            "title": "Sample Event",
            "description_teaser": "Short description",
            "description": "Longer description",
            "latitude": 55.95,
            "longitude": -3.19,
            "genre_tags": "Comedy,Fun",
            "status": "active",
            "website": "https://example.com",
            "warnings": [],
            "performances": [
                {"start": "2025-08-20 19:30:00"},
                {"start": "2025-08-21 19:30:00"},
            ],
        }
    ]

    captured = {}

    class DummyResponse:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            return None

        def json(self):
            return self._data

    def fake_get(url, timeout):
        captured["url"] = url
        captured["timeout"] = timeout
        return DummyResponse(payload)

    monkeypatch.setattr(festivals_api.requests, "get", fake_get)

    result = festivals_api.fetch_festival_events(
        event_date, festival="demofringe", limit=1
    )

    assert result["date"] == "2025-08-20"
    assert len(result["events"]) == 1
    event = result["events"][0]
    assert event.name == "Sample Event"
    assert event.description == "Short description"
    assert event.link == "https://example.com"
    assert event.location == (55.95, -3.19)
    assert event.emoji == "😂"
    assert event.event_score == pytest.approx(8.0)

    parsed = urlparse(captured["url"])  # type: ignore[index]
    assert parsed.scheme == "https"
    assert parsed.netloc == "api.edinburghfestivalcity.com"
    assert parsed.path == "/events"
    query = parse_qs(parsed.query)
    assert query["festival"] == ["demofringe"]
    assert query["limit"] == ["1"]
    assert query["key"] == ["abc123"]
    assert query["date_from"] == ["2025-08-20 00:00:00"]
    assert query["date_to"] == ["2025-08-20 23:59:59"]
    assert "signature" in query
    assert captured["timeout"] == festivals_api.DEFAULT_TIMEOUT_SECONDS


def test_fetch_festival_events_missing_credentials(monkeypatch):
    monkeypatch.delenv("EDINBURGH_FESTIVALS_API_KEY", raising=False)
    monkeypatch.delenv("EDINBURGH_FESTIVALS_SECRET_KEY", raising=False)

    with pytest.raises(festivals_api.FestivalsAPIError):
        festivals_api.fetch_festival_events(date.today())


def test_fetch_festival_events_invalid_payload(monkeypatch):
    monkeypatch.setenv("EDINBURGH_FESTIVALS_API_KEY", "abc123")
    monkeypatch.setenv("EDINBURGH_FESTIVALS_SECRET_KEY", "secret")

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"events": []}

    monkeypatch.setattr(
        festivals_api.requests,
        "get",
        lambda url, timeout: DummyResponse(),
    )

    with pytest.raises(festivals_api.FestivalsAPIError):
        festivals_api.fetch_festival_events(date.today())


@pytest.mark.integration
@pytest.mark.skipif(
    not (
        os.getenv("EDINBURGH_FESTIVALS_API_KEY")
        and os.getenv("EDINBURGH_FESTIVALS_SECRET_KEY")
    ),
    reason="LIVE test requires Edinburgh Festivals API credentials",
)
def test_fetch_festival_events_live_returns_results():
    payload = festivals_api.fetch_festival_events(date(2025, 11, 1))
    assert payload["date"] == "2025-11-01"
    assert payload["events"], "Expected live festivals API to return events"
