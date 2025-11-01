"""Client utilities for the Edinburgh Festivals Listings API."""

from __future__ import annotations

import hashlib
import hmac
import os
from datetime import date, datetime
from typing import Any, Iterable, List, Mapping, Optional, Sequence, TypedDict
from urllib.parse import urlencode

import requests

from ...schemas.events import Event

API_BASE_URL = "https://api.edinburghfestivalcity.com"
EVENTS_ENDPOINT = "/events"
DEFAULT_TIMEOUT_SECONDS = 30

Emoji = str


class FestivalsAPIError(RuntimeError):
    """Raised when the Edinburgh Festivals API cannot be queried successfully."""


class FestivalEventsPayload(TypedDict):
    """Structured response for events retrieved for a specific date."""

    date: str
    events: List[Event]


def fetch_festival_events(
    event_date: date,
    festival: Optional[str] = None,
    *,
    modified_from: Optional[str] = None,
    limit: Optional[int] = 50,
) -> FestivalEventsPayload:
    """Fetch events scheduled on `event_date` and map them to Event objects."""
    api_key, secret_key = _get_credentials()
    query_items: List[tuple[str, str]] = []

    if festival:
        query_items.append(("festival", festival))
    if modified_from:
        query_items.append(("modified_from", modified_from))
    if limit is not None:
        query_items.append(("limit", str(limit)))
    start_of_day = f"{event_date.isoformat()} 00:00:00"
    end_of_day = f"{event_date.isoformat()} 23:59:59"
    query_items.append(("date_from", start_of_day))
    query_items.append(("date_to", end_of_day))

    query_items.append(("key", api_key))
    signed_path = _build_signed_path(secret_key, EVENTS_ENDPOINT, query_items)
    url = f"{API_BASE_URL}{signed_path}"

    try:
        response = requests.get(url, timeout=DEFAULT_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FestivalsAPIError("Failed to fetch festival events") from exc

    payload = response.json()
    if not isinstance(payload, list):
        raise FestivalsAPIError("Unexpected payload format from festivals API")

    events: List[Event] = []
    for item in payload:
        if not isinstance(item, Mapping):
            continue
        event = _map_event(item)
        if event:
            events.append(event)

    return {"date": event_date.isoformat(), "events": events}


def _get_credentials() -> tuple[str, str]:
    api_key = os.getenv("EDINBURGH_FESTIVALS_API_KEY")
    secret_key = os.getenv("EDINBURGH_FESTIVALS_SECRET_KEY")
    if not api_key or not secret_key:
        raise FestivalsAPIError(
            "EDINBURGH_FESTIVALS_API_KEY and EDINBURGH_FESTIVALS_SECRET_KEY must be set"
        )
    return api_key, secret_key


def _build_signed_path(
    secret_key: str,
    endpoint: str,
    params: Sequence[tuple[str, str]],
) -> str:
    encoded_query = urlencode(params, doseq=True)
    path = f"{endpoint}?{encoded_query}" if encoded_query else endpoint
    signature = hmac.new(
        secret_key.encode("utf-8"), path.encode("utf-8"), hashlib.sha1
    ).hexdigest()
    separator = "&" if "?" in path else "?"
    return f"{path}{separator}signature={signature}"


def _parse_datetime(value: str) -> Optional[datetime]:
    candidates = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z")
    for fmt in candidates:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _map_event(item: Mapping[str, Any]) -> Optional[Event]:
    title = item.get("title")
    latitude = item.get("latitude")
    longitude = item.get("longitude")
    if not title or latitude is None or longitude is None:
        return None

    description = (
        item.get("description_teaser")
        or item.get("description")
        or "No description available."
    )
    link = item.get("website") or item.get("url")

    return Event(
        name=title,
        description=description,
        emoji=_derive_emoji(item),
        event_score=_score_event(item),
        location=(float(latitude), float(longitude)),
        link=link,
    )


def _derive_emoji(item: Mapping[str, Any]) -> Emoji:
    tag_values = _collect_tags(item)
    for tag in tag_values:
        emoji = _EMOJI_BY_TAG.get(tag)
        if emoji:
            return emoji

    festival = str(item.get("festival_id") or item.get("festival") or "").lower()
    if festival:
        festival_emoji = _FESTIVAL_EMOJI.get(festival)
        if festival_emoji:
            return festival_emoji

    return "🎉"


def _collect_tags(item: Mapping[str, Any]) -> Iterable[str]:
    tags: List[str] = []

    genre_tags = item.get("genre_tags")
    if isinstance(genre_tags, str):
        tags.extend(part.strip().lower() for part in genre_tags.split(",") if part)
    elif isinstance(genre_tags, Iterable):
        tags.extend(str(part).strip().lower() for part in genre_tags if part)

    categories = item.get("categories")
    if isinstance(categories, Mapping):
        for key in ("strand_titles", "subjects", "keywords"):
            values = categories.get(key)
            if isinstance(values, Iterable) and not isinstance(values, (str, bytes)):
                tags.extend(str(part).strip().lower() for part in values if part)

    return tags


_EMOJI_BY_TAG: Mapping[str, Emoji] = {
    "comedy": "😂",
    "dark comedy": "😂",
    "musical": "🎵",
    "music": "🎵",
    "dance": "💃",
    "ballet": "🩰",
    "theatre": "🎭",
    "theater": "🎭",
    "spoken word": "🗣️",
    "cabaret": "🎙️",
    "film": "🎬",
    "art": "🎨",
    "exhibition": "🖼️",
    "family": "👨‍👩‍👧",
    "kids": "🧒",
    "circus": "🎪",
    "magic": "🪄",
    "dance-party": "🎉",
}

_FESTIVAL_EMOJI: Mapping[str, Emoji] = {
    "demofringe": "🎭",
    "fringe": "🎭",
    "book": "📚",
    "science": "🔬",
    "jazz": "🎷",
    "film": "🎬",
}


def _score_event(item: Mapping[str, Any]) -> float:
    base_score = 8.0 if item.get("status") == "active" else 5.0
    if item.get("disabled"):
        base_score -= 2.0
    warnings = item.get("warnings")
    if isinstance(warnings, Iterable) and not isinstance(warnings, (str, bytes)):
        if any(bool(warning) for warning in warnings):
            base_score -= 0.5
    return max(0.0, min(10.0, float(base_score)))


__all__ = ["fetch_festival_events", "FestivalsAPIError", "FestivalEventsPayload"]
