from __future__ import annotations

from typing import List

from ..models import Event
from .context_aggregator import ContextAggregator
from .llm import LLM


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
        sample_events = LLM()._get_fallback_events()

        if not preferences:
            return sample_events

        # Simple preference filter demo; extend to fuzzy matching as needed.
        filtered = [
            event for event in sample_events if preferences in event.description.lower()
        ]
        return filtered or sample_events

