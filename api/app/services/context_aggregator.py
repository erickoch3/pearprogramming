from collections.abc import Mapping
from typing import Any


class ContextAggregator:
    """Collects context data used to tailor event recommendations."""

    def gather_context(self, response_preferences: str | None) -> Mapping[str, Any]:
        """Aggregate request preferences with default metadata."""
        # In a real implementation this would query user profiles, calendars, etc.
        normalized_preferences = (response_preferences or "").strip().lower()
        return {
            "preferences": normalized_preferences,
            "default_city": "Sampleville",
            "season": "spring",
        }

