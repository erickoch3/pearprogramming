from __future__ import annotations

import logging
import os
import re
import threading
import time
from collections.abc import Mapping
from datetime import date
from typing import Any, Optional

import requests
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from requests import Session

load_dotenv()

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency may fail at import time
    from ..utils.scrapers.scrape_eventbrite import (  # type: ignore[attr-defined]
        get_events as _eventbrite_get_events,
    )
except Exception as exc:  # pragma: no cover
    _eventbrite_get_events = None  # type: ignore[assignment]
    logger.debug("Eventbrite scraper import failed: %s", exc)

try:  # pragma: no cover - optional dependency may fail at import time
    from ..utils.scrapers.scrape_tweets import (  # type: ignore[attr-defined]
        get_tweets as _tweets_get_tweets,
    )
except Exception as exc:  # pragma: no cover
    _tweets_get_tweets = None  # type: ignore[assignment]
    logger.debug("Tweet scraper import failed: %s", exc)

from .scrapers import (
    FestivalEventsPayload,
    FestivalsAPIError,
    fetch_festival_events,
)


class WeatherFetchError(RuntimeError):
    """Raised when the weather provider cannot return a usable payload."""


_SESSION = Session()
_WEATHER_CACHE_LOCK = threading.Lock()
_FESTIVAL_CACHE_LOCK = threading.Lock()
_WEATHER_CACHE_TTL_SECONDS = 600  # 10 minutes
_FESTIVAL_CACHE_TTL_SECONDS = 1800  # 30 minutes
_WEATHER_CACHE: dict[tuple[str, str, str], tuple[float, Mapping[str, Any]]] = {}
_FESTIVAL_CACHE: dict[
    tuple[str, Optional[str], Optional[int]], tuple[float, FestivalEventsPayload]
] = {}


def _estimate_season(target_date: date) -> str:
    month = target_date.month
    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    return "autumn"


class ContextAggregator:
    """Collects context data used to tailor event recommendations."""

    def get_todays_weather_forecast(
        self,
        city: str,
        country_code: str,
        target_date: date,
    ) -> Mapping[str, Any]:
        """Return current weather conditions for the given city."""
        cache_key = (city, country_code, target_date.isoformat())
        now = time.monotonic()
        with _WEATHER_CACHE_LOCK:
            cached = _WEATHER_CACHE.get(cache_key)
            if cached and now - cached[0] < _WEATHER_CACHE_TTL_SECONDS:
                return cached[1]

        weather_payload = self._fetch_weather_from_api(city, country_code)
        weather_payload_with_date = dict(weather_payload)
        weather_payload_with_date["date"] = target_date.isoformat()

        with _WEATHER_CACHE_LOCK:
            _WEATHER_CACHE[cache_key] = (now, weather_payload_with_date)

        return weather_payload_with_date

    def gather_context(
        self,
        response_preferences: Optional[str],
        *,
        target_date: Optional[date] = None,
        default_city: str = "Edinburgh",
        default_country_code: str = "GB",
        festival: Optional[str] = None,
        festival_limit: Optional[int] = 25,
    ) -> Mapping[str, Any]:
        """Aggregate request preferences, weather, and festival events."""
        raw_preferences = (response_preferences or "").strip()
        normalized_preferences = raw_preferences.lower()
        preference_keywords = self._extract_preference_keywords(raw_preferences)
        resolved_date = target_date or date.today()

        weather_payload: Optional[Mapping[str, Any]] = None
        weather_error: Optional[str] = None

        festival_events: FestivalEventsPayload = {
            "date": resolved_date.isoformat(),
            "events": [],
        }
        festival_identifier = (
            festival
            if festival is not None
            else os.getenv("EDINBURGH_FESTIVALS_DEFAULT_FESTIVAL") or None
        )
        # Always include Eventbrite-scraped events; require scraper to be available.
        eventbrite_events: list[Any] = []
        eventbrite_error: Optional[str] = None
        if _eventbrite_get_events is None:
            raise RuntimeError(
                "Eventbrite scraper is unavailable. Install and configure the scraper dependency."
            )

        weather_future = None
        festival_future = None
        eventbrite_future = None

        with ThreadPoolExecutor(max_workers=3) as executor:
            weather_future = executor.submit(
                self.get_todays_weather_forecast,
                default_city,
                default_country_code,
                resolved_date,
            )
            festival_future = executor.submit(
                self._get_festival_events_cached,
                resolved_date,
                festival_identifier,
                festival_limit,
            )
            location = default_city
            today_only = resolved_date == date.today()
            eventbrite_future = executor.submit(
                _eventbrite_get_events,
                location,
                today_only=today_only,
            )

        if weather_future is not None:
            try:
                weather_payload = weather_future.result()
            except WeatherFetchError as exc:
                logger.warning("Weather fetch failed: %s", exc)
                weather_error = str(exc)
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.warning("Unexpected weather fetch failure: %s", exc)
                weather_error = str(exc)

        if festival_future is not None:
            try:
                festival_events = festival_future.result()
            except FestivalsAPIError as exc:
                logger.warning("Festival fetch failed: %s", exc)
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.warning("Unexpected festival fetch failure: %s", exc)

        if eventbrite_future is not None:
            try:
                eventbrite_events = eventbrite_future.result()
            except Exception as exc:  # pragma: no cover - network/env dependent
                logger.warning("Eventbrite fetch failed: %s", exc)
                eventbrite_error = str(exc)

        return {
            "date": resolved_date.isoformat(),
            "preferences": normalized_preferences,
            "preferences_raw": raw_preferences,
            "preferences_normalized": normalized_preferences,
            "preference_keywords": preference_keywords,
            "has_preferences": bool(raw_preferences),
            "city": default_city,
            "weather": weather_payload,
            "weather_error": weather_error,
            "festival_events": festival_events,
            "eventbrite_events": eventbrite_events,
            "eventbrite_error": eventbrite_error,
        }

    @staticmethod
    def _extract_preference_keywords(preferences: str) -> list[str]:
        """Return a lightweight set of keywords describing the user's preferences."""
        if not preferences:
            return []

        tokens = re.split(r"[^\w]+", preferences.lower())
        return [token for token in tokens if token and len(token) > 2]

    def _fetch_weather_from_api(
        self,
        city: str,
        country_code: str,
    ) -> Mapping[str, Any]:
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not api_key:
            raise WeatherFetchError("OPENWEATHERMAP_API_KEY is not configured.")

        try:
            weather_response = _SESSION.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": f"{city},{country_code}",
                    "units": "metric",
                    "appid": api_key,
                },
                timeout=10,
            )
            weather_response.raise_for_status()
        except requests.RequestException as exc:
            raise WeatherFetchError(
                f"Failed to fetch weather for location '{city},{country_code}': {exc}"
            ) from exc

        weather_response_json = weather_response.json()
        if weather_response_json.get("cod") not in (200, "200", None):
            message = weather_response_json.get(
                "message", "Unknown error from weather API"
            )
            raise WeatherFetchError(
                f"Weather API error for '{city},{country_code}': {message}"
            )

        return {
            "temperature": weather_response_json.get("main", {}).get("temp"),
            "feels_like": weather_response_json.get("main", {}).get("feels_like"),
            "humidity": weather_response_json.get("main", {}).get("humidity"),
            "wind_speed": weather_response_json.get("wind", {}).get("speed"),
            "percent_cloudiness": weather_response_json.get("clouds", {}).get("all"),
            "rain_mm_per_h": weather_response_json.get("rain"),
            "snow_mm_per_h": weather_response_json.get("snow"),
        }

    def _get_festival_events_cached(
        self,
        target_date: date,
        festival_identifier: Optional[str],
        festival_limit: Optional[int],
    ) -> FestivalEventsPayload:
        cache_key = (
            target_date.isoformat(),
            festival_identifier,
            festival_limit,
        )
        now = time.monotonic()
        with _FESTIVAL_CACHE_LOCK:
            cached = _FESTIVAL_CACHE.get(cache_key)
            if cached and now - cached[0] < _FESTIVAL_CACHE_TTL_SECONDS:
                return cached[1]

        events = fetch_festival_events(
            target_date,
            festival=festival_identifier,
            limit=festival_limit,
        )

        with _FESTIVAL_CACHE_LOCK:
            _FESTIVAL_CACHE[cache_key] = (now, events)

        return events
