"""Service layer components used by the FastAPI application.

This module avoids eagerly importing optional dependencies (for example the
LLM stack used by ``ActivitySuggestionGenerator``) so that modules without those
requirements can still be imported in isolation, such as during tests.
"""

from typing import Any

__all__ = ["ActivitySuggestionGenerator", "ContextAggregator", "fetch_festival_events"]


def __getattr__(name: str) -> Any:
    if name == "ActivitySuggestionGenerator":
        from .activity_suggestion_generator import ActivitySuggestionGenerator

        return ActivitySuggestionGenerator
    if name == "ContextAggregator":
        from .context_aggregator import ContextAggregator

        return ContextAggregator
    if name == "fetch_festival_events":
        from .scrapers import fetch_festival_events

        return fetch_festival_events
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
