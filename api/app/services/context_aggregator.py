from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any, Optional

import requests
from dotenv import load_dotenv

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
        get_events as _tweets_get_events,
    )
except Exception as exc:  # pragma: no cover
    _tweets_get_events = None  # type: ignore[assignment]
    logger.debug("Tweet scraper import failed: %s", exc)

from .scrapers import (
    FestivalEventsPayload,
    FestivalsAPIError,
    fetch_festival_events,
)


class WeatherFetchError(RuntimeError):
    """Raised when the weather provider cannot return a usable payload."""


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
        load_dotenv()
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not api_key:
            raise WeatherFetchError("OPENWEATHERMAP_API_KEY is not configured.")

        try:
            coord_response = requests.get(
                "https://api.openweathermap.org/geo/1.0/direct",
                params={"q": f"{city},{country_code}", "limit": 1, "appid": api_key},
                timeout=10,
            )
            coord_response.raise_for_status()
        except requests.RequestException as exc:
            raise WeatherFetchError(
                f"Failed to geocode location '{city},{country_code}': {exc}"
            ) from exc

        coord_data = coord_response.json()
        if not (isinstance(coord_data, list) and coord_data):
            raise WeatherFetchError(
                f"No coordinates returned for '{city},{country_code}'."
            )

        first = coord_data[0]
        lat = first.get("lat")
        lon = first.get("lon")
        if lat is None or lon is None:
            raise WeatherFetchError(
                f"Incomplete coordinates returned for '{city},{country_code}'."
            )

        try:
            weather_response = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "units": "metric",
                    "appid": api_key,
                },
                timeout=10,
            )
            weather_response.raise_for_status()
        except requests.RequestException as exc:
            raise WeatherFetchError(
                f"Failed to fetch weather for coordinates ({lat}, {lon}): {exc}"
            ) from exc

        weather_response_json = weather_response.json()
        if weather_response_json.get("cod") not in (200, "200", None):
            message = weather_response_json.get(
                "message", "Unknown error from weather API"
            )
            raise WeatherFetchError(
                f"Weather API error for ({lat}, {lon}): {message}"
            )

        target_iso = target_date.isoformat()
        return {
            "date": target_iso,
            "temperature": weather_response_json.get("main", {}).get("temp"),
            "feels_like": weather_response_json.get("main", {}).get("feels_like"),
            "humidity": weather_response_json.get("main", {}).get("humidity"),
            "wind_speed": weather_response_json.get("wind", {}).get("speed"),
            "percent_cloudiness": weather_response_json.get("clouds", {}).get("all"),
            "rain_mm_per_h": weather_response_json.get("rain"),
            "snow_mm_per_h": weather_response_json.get("snow"),
        }

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
        normalized_preferences = (response_preferences or "").strip().lower()
        resolved_date = target_date or date.today()

        weather_payload: Optional[Mapping[str, Any]]
        weather_error: Optional[str] = None
        try:
            weather_payload = self.get_todays_weather_forecast(
                default_city, default_country_code, resolved_date
            )
        except WeatherFetchError as exc:
            logger.warning("Weather fetch failed: %s", exc)
            weather_payload = None
            weather_error = str(exc)

        festival_events: FestivalEventsPayload = {
            "date": resolved_date.isoformat(),
            "events": [],
        }
        festival_identifier = (
            festival
            if festival is not None
            else os.getenv("EDINBURGH_FESTIVALS_DEFAULT_FESTIVAL") or None
        )
        try:
            festival_events = fetch_festival_events(
                resolved_date,
                festival=festival_identifier,
                limit=festival_limit,
            )
        except FestivalsAPIError as exc:
            logger.warning("Festival fetch failed: %s", exc)

        # Optionally include Eventbrite-scraped events when the optional scraper
        # dependency is available and credentials are configured.
        eventbrite_events: list[Any] = []
        eventbrite_error: Optional[str] = None
        if _eventbrite_get_events is not None:
            try:
                # Prefer a location that definitely works with the scraper. Using just the
                # city still yields a valid Eventbrite discovery URL and helps geocoding
                # via the location_context.
                location = default_city
                # Limit to today's events only if the requested date is today; otherwise
                # return the broader set (the scraper does not support arbitrary dates).
                today_only = resolved_date == date.today()
                eventbrite_events = _eventbrite_get_events(
                    location,
                    today_only=today_only,
                )
            except Exception as exc:  # pragma: no cover - network/env dependent
                logger.warning("Eventbrite fetch failed: %s", exc)
                eventbrite_error = str(exc)
        else:
            logger.debug("Eventbrite scraper not available; skipping Eventbrite events")
        
        # Optionally include events from Twitter API when the optional scraper
        # dependency is available and credentials are configured.
        twitter_events: list[Any] = []
        twitter_error: Optional[str] = None
        if _tweets_get_events is not None:
            try:
                twitter_events = _tweets_get_events()
            except Exception as exc:  # pragma: no cover - network/env dependent
                logger.warning("Twitter fetch failed: %s", exc)
                twitter_error = str(exc)
        else:
            logger.debug("Twitter scraper not available; skipping Twitter events")

        return {
            "date": resolved_date.isoformat(),
            "preferences": normalized_preferences,
            "city": default_city,
            "weather": weather_payload,
            "weather_error": weather_error,
            "festival_events": festival_events,
            "eventbrite_events": eventbrite_events,
            "eventbrite_error": eventbrite_error,
            "twitter_events": twitter_events,
            "twitter_error": twitter_error
        }
