import os
import sys

import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from api.app.schemas.events import Event  # pylint: disable=wrong-import-position
from api.app.services.activity_suggestion_generator import (  # pylint: disable=wrong-import-position
    ActivitySuggestionGenerator,
)


class DummyAggregator:
    def __init__(self):
        self.called_with = None

    def gather_context(self, response_preferences):
        self.called_with = response_preferences
        return {
            "preferences": response_preferences or "",
            "festival_events": {"date": "2025-11-02", "events": []},
            "eventbrite_events": [],
        }


class DummyLLM:
    def __init__(self):
        self.invocations = []

    def generate_event_suggestions(self, *, context, max_events):
        self.invocations.append(
            {"context": context, "max_events": max_events}
        )
        return [
            Event(
                name="LLM Crafted Event",
                description="Structured output originating from the language model.",
                emoji="🎉",
                event_score=9.1,
                location=(55.95, -3.19),
                link="https://example.com/llm-event",
            )
        ]


def test_generate_suggestions_uses_llm(monkeypatch):
    monkeypatch.delenv("MOCK", raising=False)
    aggregator = DummyAggregator()
    generator = ActivitySuggestionGenerator(context_aggregator=aggregator)

    stub_llm = DummyLLM()
    monkeypatch.setattr(generator, "_get_llm", lambda: stub_llm)

    events = generator.generate_suggestions(number_events=1, response_preferences="music")

    assert aggregator.called_with == "music"
    assert len(stub_llm.invocations) == 1
    assert stub_llm.invocations[0]["context"]["preferences"] == "music"
    assert events[0].name == "LLM Crafted Event"
    assert events[0].event_score == pytest.approx(9.1)
