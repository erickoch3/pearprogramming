from __future__ import annotations

from typing import List

from ..schemas.events import Event

MOCK_EVENTS: List[Event] = [
    Event(
        name="Sunrise Arthurs Seat Hike",
        description="Catch the sunrise over Edinburgh with a guided early morning climb.",
        emoji="🌄",
        location=(1.5, -1.2),
        event_score=9.2,
        link="https://www.visitscotland.com/info/events/edinburgh-sunrise-hike-p123456",
    ),
    Event(
        name="Leith Street Food Market",
        description="Sample dishes from 20+ local vendors, live music, and craft stalls.",
        emoji="🍜",
        location=(0.3, 1.8),
        event_score=8.7,
        link="https://edinburghmarkets.com/leith-street-food",
    ),
    Event(
        name="Meadows Community Yoga",
        description="Free outdoor yoga session suitable for all levels - bring a mat!",
        emoji="🧘",
        location=(0.2, -0.8),
        event_score=8.1,
        link="https://facebook.com/events/edinburgh-meadows-yoga",
    ),
    Event(
        name="Portobello Beach Cleanup",
        description="Join local volunteers to help clean the shoreline followed by coffee.",
        emoji="🧹",
        location=(8.0, 0.2),
        event_score=8.9,
        link="https://keepedinburghbeautiful.org/portobello-cleanup",
    ),
    Event(
        name="Stockbridge Farmers Market",
        description="Weekly market with artisan produce, fresh bakes, and local crafts.",
        emoji="🧺",
        location=(-1.2, 0.8),
        event_score=8.4,
        link="https://stockbridgefarmersmarket.co.uk",
    ),
    Event(
        name="Water of Leith Cycle",
        description="Guided family-friendly cycle along Water of Leith walkway.",
        emoji="🚴",
        location=(-1.8, 0.5),
        event_score=7.8,
    ),
    Event(
        name="Calton Hill Sketch Walk",
        description="Urban sketching meetup—bring pencils and capture the skyline.",
        emoji="✏️",
        location=(0.8, 0.3),
        event_score=8.0,
    ),
    Event(
        name="Grassmarket Storytelling Night",
        description="Local storytellers share Scottish folklore by candlelight.",
        emoji="📖",
        location=(-0.5, -0.3),
        event_score=8.6,
    ),
]


def get_mock_events(limit: int) -> List[Event]:
    """Return the configured mock events up to the requested limit."""
    bounded_limit = max(0, limit)
    return MOCK_EVENTS[:bounded_limit]
