from __future__ import annotations

from typing import List

from ..models import Event
from .context_aggregator import ContextAggregator


class ActivitySuggestionGenerator:
    """Generates activity suggestions using contextual data."""

    def __init__(self, context_aggregator: ContextAggregator) -> None:
        self._context_aggregator = context_aggregator

    def generate_suggestions(
        self, number_events: int, response_preferences: str | None
    ) -> List[Event]:
        """Produce event recommendations matching the caller's preferences."""
        context = self._context_aggregator.gather_context(response_preferences)
        preferences = context["preferences"]

        ranked_events = self._get_ranked_events(preferences)
        return ranked_events[:number_events]

    def _get_ranked_events(self, preferences: str) -> List[Event]:
        """Return a preference-aware ordered list of candidate events."""
        # Placeholder scoring showcasing structure; replace with ML or rules later.
        sample_events: List[Event] = [
            Event(
                location=(12, 34),
                name="Community Coding Jam",
                emoji="💻",
                event_score=9,
                description="Pair up with local devs for a collaborative hack session.",
                link="https://example.com/community-coding-jam",
            ),
            Event(
                location=(5, 18),
                name="Art Walk Downtown",
                emoji="🎨",
                event_score=7,
                description="Explore pop-up galleries with live demos from local artists.",
            ),
            Event(
                location=(22, 9),
                name="Gourmet Food Truck Rally",
                emoji="🌮",
                event_score=8,
                description="Taste bites from featured chefs with live music.",
            ),
            Event(
                location=(3, 42),
                name="Outdoor Movie Night",
                emoji="🎬",
                event_score=6,
                description="Bring a blanket for a classic film under the stars.",
                link="https://example.com/outdoor-movie-night",
            ),
        ]

        if not preferences:
            return sample_events

        # Simple preference filter demo; extend to fuzzy matching as needed.
        filtered = [
            event for event in sample_events if preferences in event.description.lower()
        ]
        return filtered or sample_events

