from __future__ import annotations

import json
import logging
import os
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, List

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

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
                "You transform contextual information into structured event recommendations that reflect the caller's preferences. "
                "Always reply using the EventList schema with fields: name, description, emoji, "
                "event_score (0-10), location (x,y coordinates), and optional link. "
                "IMPORTANT: The emoji field must contain exactly ONE single emoji character that best represents the event (e.g., 🎭 for theater, 🎵 for music, 🍕 for food). "
                "Do NOT use multiple emojis, text, or emoji combinations. "
                "The context payload includes user preference signals under keys such as 'preferences_raw', "
                "'preferences', 'preferences_normalized', and 'preference_keywords'. Use these to select and score events: "
                "scores of 9-10 indicate strong alignment, 6-8 partial alignment, and 0-5 weak or fallback options. "
                "Do not return events that conflict with the stated preferences unless no aligned options exist."
            ),
        ),
        (
            "human",
            "Context:\n{context}\n\nPrioritize the user's stated preferences when choosing events. "
            "Return up to {max_events} high-quality, preference-aligned events. "
            "Remember: use exactly one emoji per event.",
        ),
    ]
)


class LLM:
    """Service for interacting with OpenAI models for event suggestions."""

    def __init__(self) -> None:
        load_dotenv(dotenv_path=os.getenv("DOTENV_PATH", ".env"), override=False)
        self._model_candidates: Sequence[str] = tuple(self._build_model_list())
        if not self._model_candidates:
            raise RuntimeError(
                "No OpenAI models configured. Set OPENAI_MODEL or OPENAI_MODEL_FALLBACKS."
            )
        self._active_model: str | None = None

    def generate_event_suggestions(
        self,
        context: Any,
        *,
        max_events: int = 8,
    ) -> List[Event]:
        """Generate structured event suggestions using the first available model."""
        context_text = self._format_context(context)
        last_error: Exception | None = None

        for model_name in self._model_candidates:
            try:
                structured_chain = self._build_chain(model_name)
                result: EventList = structured_chain.invoke(
                    {"context": context_text, "max_events": max_events}
                )
                self._active_model = model_name
                return list(result.events)
            except Exception as exc:  # pragma: no cover - network dependent
                last_error = exc
                logger.warning(
                    "Model %s failed: %s. Trying next candidate if available.",
                    model_name,
                    exc,
                )

        raise RuntimeError(
            "All configured OpenAI models failed. "
            "Last error: {}".format(last_error or "Unknown error")
        )

    def _build_chain(self, model_name: str):
        """Create a structured output chain for the requested model."""
        llm = ChatOpenAI(model=model_name)
        structured_llm = llm.with_structured_output(EventList)
        return _PROMPT | structured_llm

    @staticmethod
    def _format_context(context: Any) -> str:
        """Coerce arbitrary context payloads into a readable string for prompting."""
        if isinstance(context, str):
            return context
        if isinstance(context, Mapping):
            try:
                return json.dumps(context, indent=2)
            except TypeError:
                return str(dict(context))
        if isinstance(context, Iterable) and not isinstance(context, (bytes, bytearray)):
            return "\n".join(str(item) for item in context)
        return str(context)

    @staticmethod
    def _build_model_list() -> List[str]:
        """Return the ordered list of model names to attempt."""
        configured = os.getenv("OPENAI_MODEL")
        fallbacks = os.getenv("OPENAI_MODEL_FALLBACKS")

        models: List[str] = []
        if configured:
            models.extend(_split_models(configured))
        else:
            models.append(_DEFAULT_MODEL)

        if fallbacks:
            models.extend(_split_models(fallbacks))
        else:
            models.extend(model for model in _MODEL_FALLBACKS if model not in models)

        # Remove duplicates while preserving order
        seen: set[str] = set()
        deduped: List[str] = []
        for model in models:
            if model and model not in seen:
                seen.add(model)
                deduped.append(model)
        return deduped

    @staticmethod
    def _get_fallback_events(limit: int = 8) -> List[Event]:
        """Return fallback events bundled with the application."""
        return get_mock_events(limit)


def _split_models(raw: str) -> List[str]:
    """Split a comma- or whitespace-separated string of model names."""
    return [chunk.strip() for chunk in raw.replace(",", " ").split() if chunk.strip()]
