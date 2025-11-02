from ..data.mock_events import get_mock_events
from ..schemas.events import Event, EventList
from .context_aggregator import ContextAggregator

from langchain.agents import create_agent
from dotenv import load_dotenv
from pydantic import ValidationError

import os
from typing import Optional


class ActivitySuggestionGenerator:
    """Generates activity suggestions using contextual data."""

    def __init__(self, context_aggregator: ContextAggregator) -> None:
        load_dotenv()
        self._context_aggregator = context_aggregator
        self._event_suggester = create_agent(
            model="gpt-4.1-mini",
            response_format=EventList,
        )
        self._mock_mode_enabled = os.getenv("MOCK") == "1"

    def generate_suggestions(
        self, number_events: int, response_preferences: Optional[str]
    ) -> list[Event]:

        if self._mock_mode_enabled:
            events = get_mock_events(number_events)
            if response_preferences:
                normalized = response_preferences.strip().lower()
                filtered = [
                    event
                    for event in events
                    if normalized in event.name.lower()
                    or normalized in event.description.lower()
                ]
                events = filtered or events
            return events

        context = self._context_aggregator.gather_context(response_preferences)
        model_response = self._event_suggester.invoke({
            "messages": [{
                "role": "user", 
                "content": f"Extract event objects from the following context:\n\n{context}"
            }]
        })

        try:
            structured = EventList.model_validate(model_response["structured_response"])
        except ValidationError as e:
            raise TypeError("structured model response is not a valid `EventList`") from e

        return structured.events

