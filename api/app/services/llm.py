from __future__ import annotations

import json
import logging
import os
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, List

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from ..data.mock_events import get_mock_events
from ..schemas.events import Event, EventList

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "gpt-4.1-mini"
_MODEL_FALLBACKS = ("gpt-4.1", "gpt-4o-mini", "gpt-4o")

_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You transform contextual information into structured event recommendations. "
                "Always reply using the EventList schema with fields: name, description, emoji, "
                "event_score (0-10), location (x,y coordinates), and optional link."
            ),
        ),
        (
            "human",
            "Context:\n{context}\n\nReturn up to {max_events} high-quality events.",
        ),
    ]
)


class LLM:
    """Service for interacting with OpenAI models for event suggestions."""

    def __init__(self) -> None:
        self.agent = create_agent(
            model="gpt-5",
            response_format=EventList,
        )

    def generate_event_suggestions(
        self,
        context: Any,
    ) -> List[Event]:
        """Generate structured event suggestions using the first available model."""
        model_response = self.agent.invoke({
            "messages": [{"role": "user", "content": f"Extract event objects from the following context:\n\n{context}"}]
        })
        return model_response["structured_response"].events

    @staticmethod
    def _get_fallback_events(limit: int = 8) -> List[Event]:
        """Return fallback events bundled with the application."""
        return get_mock_events(limit)

