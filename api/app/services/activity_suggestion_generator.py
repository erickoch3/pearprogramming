from __future__ import annotations

import os
import re
from typing import List, Optional

from ..schemas.events import Event
from ..data.mock_events import get_mock_events
from .context_aggregator import ContextAggregator

try:
    from .llm import LLM
except Exception as exc:  # pragma: no cover - optional dependency for mock mode
    LLM = None  # type: ignore[assignment]
    _llm_import_error: Optional[Exception] = exc
else:  # pragma: no cover - import success path exercised in integration flow
    _llm_import_error = None

TEST_CONTEXT = """
At (12, -5), the Riverside Night Market 🌙 is buzzing; I’d give it an 8 because the street food stalls change weekly and there’s live acoustic sets drifting over the riverbank. If you need the vendor map, peek at https://riversidenightmarket.example.
Over at (-3, 14), there’s the Pop-Up Book Garden 📚—I’m calling it a 7 since the used-book swap is sizable and the kid craft corner runs all afternoon; lots of rare sci-fi paperbacks.
Coordinates (0, 0) land you in Central Plaza for Sunrise Yoga 🧘‍♀️; it’s a calm 6, short and sweet, led by a local instructor who cues breathwork for beginners; bring a mat and water.
Head to (25, 9) for the Bricklane Street Art Walk 🎨; solid 9, with a guide who knows the backstory behind the newest murals and the tour ends at a tiny espresso bar tucked in an alley. Sign-ups live at https://citywalks.example/streetart.
At (-18, -2), the Retro Arcade Free-Play 👾 is a 7; machines are on free credit from 6–9pm, and they’re running a quick Pac-Man high-score challenge with silly prizes.
If you’re at (7, 22), don’t miss the Rooftop Salsa Social 💃; I’d rate it an 8 for the sunset timing and the beginner crash course during the first half-hour; shoes with smooth soles recommended. Details: https://salsasunset.example.
Swing by (31, -11) for the Community Potluck & Recipe Swap 🥘; call it a 6—friendly crowd, emphasis on vegetarian mains, and they print a mini zine of contributed recipes at the end.
At (-7, 3) there’s the Indie Film Microfest 🎬; this one’s a 9 due to the director Q&A and a surprise 16mm screening in the courtyard. Trailer links and schedule at https://microfest.example.
The Lakeside Herb Foraging Ramble 🌿 sets off from (-2, -9); I’d put it at a 5 for casual learners—short walk, ID basics, and a tiny tasting of infused honeys back at the trailhead.
At (15, 4), the Board Game Café Open Table 🎲 is a cozy 6; staff teach two new strategy games on the hour, and there’s a quiet room if you want longer campaigns. Menu and booking: https://meeplecorner.example.
"""


class ActivitySuggestionGenerator:
    """Generates activity suggestions using contextual data."""

    def __init__(self, context_aggregator: ContextAggregator) -> None:
        self._context_aggregator = context_aggregator
        self._mock_mode_enabled = os.getenv("MOCK") == "1"
        self._llm_instance: Optional[LLM] = None

    def generate_suggestions(
        self, number_events: int, response_preferences: Optional[str]
    ) -> List[Event]:
        """Produce event recommendations matching the caller's preferences."""
        if self._mock_mode_enabled:
            events = [event.model_copy(deep=True) for event in get_mock_events(number_events)]
            tokens = _tokenize_preferences(response_preferences)
            if tokens:
                for event in events:
                    event_text = f"{event.name} {event.description}".lower()
                    match_strength = _match_ratio(event_text, tokens)
                    event.event_score = _score_with_preferences(
                        baseline=event.event_score,
                        match_ratio=match_strength,
                    )
                events.sort(key=lambda item: item.event_score, reverse=True)
            return events

        if LLM is None:  # pragma: no cover - exercised when optional deps missing
            raise RuntimeError(
                "LLM backend is unavailable. Install the required dependencies or run the API with MOCK=1."
            ) from _llm_import_error

        assert LLM is not None  # mypy/time-of-check guard
        llm = self._get_llm()
        # context = TEST_CONTEXT
        context = self._context_aggregator.gather_context(response_preferences)

        ranked_events = llm.generate_event_suggestions(
            context=context, max_events=number_events
        )
        return ranked_events

    def _get_ranked_events(self, preferences: str) -> List[Event]:
        """Return a preference-aware ordered list of candidate events."""
        if LLM is None:  # pragma: no cover - exercised when optional deps missing
            raise RuntimeError(
                "LLM backend is unavailable. Install the required dependencies or run the API with MOCK=1."
            ) from _llm_import_error

        llm = self._get_llm()
        sample_events = llm._get_fallback_events()

        if not preferences:
            return sample_events

        # Simple preference filter demo; extend to fuzzy matching as needed.
        filtered = [
            event for event in sample_events if preferences in event.description.lower()
        ]
        return filtered or sample_events

    def _get_llm(self) -> LLM:
        assert LLM is not None  # appease type checkers
        if self._llm_instance is None:
            self._llm_instance = LLM()
        return self._llm_instance


def _tokenize_preferences(preferences: Optional[str]) -> list[str]:
    if not preferences:
        return []

    tokens = re.split(r"[^\w]+", preferences.lower())
    return [token for token in tokens if token and len(token) > 2]


def _match_ratio(text: str, tokens: list[str]) -> float:
    if not tokens:
        return 0.0

    matches = sum(1 for token in tokens if token in text)
    return matches / len(tokens)


def _score_with_preferences(*, baseline: float, match_ratio: float) -> float:
    """Blend the baseline event score with the preference alignment signal."""
    if match_ratio <= 0:
        adjusted = baseline * 0.3 + 2.0
    else:
        preference_anchor = 3.0 + 7.0 * match_ratio
        adjusted = baseline * 0.3 + preference_anchor * 0.7
    return round(max(0.0, min(10.0, adjusted)), 1)
