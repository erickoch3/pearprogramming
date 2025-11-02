from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

class Location(BaseModel):
    x: float = Field(..., description="x coord")
    y: float = Field(..., description="y coord")

    def __eq__(self, other: object) -> bool:  # pragma: no cover - tiny helper
        if isinstance(other, Location):
            return self.x == other.x and self.y == other.y
        if isinstance(other, (tuple, list)) and len(other) == 2:
            return self.x == other[0] and self.y == other[1]
        return NotImplemented

class Event(BaseModel):
    """Represents a suggested activity."""

    location: Location = Field(..., description="Location coordinates where x is latitude and y is longitude")
    name: str = Field(..., description="Human-readable name for the event")
    emoji: str = Field(..., description="Emoji summarizing the event vibe")
    event_score: float = Field(
        ...,
        ge=0,
        le=10,
        description="Score representing confidence or suitability",
    )
    description: str = Field(..., description="Short description of the event")
    link: Optional[str] = Field(
        default=None, description="Optional URL for additional event information"
    )

    @field_validator("location", mode="before")
    @classmethod
    def _coerce_location(cls, value: object) -> object:
        """Allow passing bare xy tuples/lists for convenience."""
        if isinstance(value, (tuple, list)) and len(value) == 2:
            return {"x": value[0], "y": value[1]}
        return value

class EventList(BaseModel):
    events: List[Event] = Field(..., description="List of events.")

class GetEventRecommendationsRequest(BaseModel):
    """Request payload for generating event recommendations."""

    number_events: int = Field(
        ...,
        ge=1,
        le=25,
        description="Number of event suggestions desired",
    )
    response_preferences: Optional[str] = Field(
        default=None,
        description="Optional freeform preferences used to tailor suggestions",
    )


class GetEventRecommendationsResponse(BaseModel):
    """Response payload containing recommended events."""

    events: List[Event] = Field(default_factory=list, description="Recommended events")
