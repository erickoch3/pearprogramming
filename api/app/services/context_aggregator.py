from collections.abc import Mapping
from typing import Any

from app.utils.scrapers.scrape_eventbrite import get_events


class ContextAggregator:
    """Collects context data used to tailor event recommendations."""

    def gather_context(self, response_preferences: str | None) -> Mapping[str, Any]:
        """Aggregate request preferences with default metadata."""
        # In a real implementation this would query user profiles, calendars, etc.
        normalized_preferences = (response_preferences or "").strip().lower()
        events_list  = get_events("Edinburgh, United Kingdom", today_only=True) # return a list of events which are basically dictionaries with the following keys: location_name, activity_name, latitude, longitude, time
        return {
            "preferences": normalized_preferences,
            "default_city": "Edinburgh",
            "season": "spring",
            "events": events_list,
        }

