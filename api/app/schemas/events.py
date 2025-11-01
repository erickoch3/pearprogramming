from typing import Optional, Tuple

from pydantic import BaseModel, Field


class Event(BaseModel):
    """Represents a suggested activity."""

    location: Tuple[float, float] = Field(
        ..., description="Cartesian location coordinates"
    )
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

    events: list[Event] = Field(default_factory=list, description="Recommended events")
