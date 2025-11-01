from fastapi import Depends, FastAPI

from .models import GetEventRecommendationsRequest, GetEventRecommendationsResponse
from .routers import auth
from .services.activity_suggestion_generator import ActivitySuggestionGenerator
from .services.context_aggregator import ContextAggregator

app = FastAPI(title="Pear Programming API", version="0.1.0")

# Include routers
app.include_router(auth.router)


def get_context_aggregator() -> ContextAggregator:
    """Provide a ContextAggregator instance for dependency injection."""
    return ContextAggregator()


def get_activity_suggestion_generator(
    aggregator: ContextAggregator = Depends(get_context_aggregator),
) -> ActivitySuggestionGenerator:
    """Provide an ActivitySuggestionGenerator configured with the aggregator."""
    return ActivitySuggestionGenerator(context_aggregator=aggregator)


@app.post(
    "/events/recommendations",
    response_model=GetEventRecommendationsResponse,
    summary="Generate activity recommendations",
)
async def get_event_recommendations(
    request: GetEventRecommendationsRequest,
    generator: ActivitySuggestionGenerator = Depends(get_activity_suggestion_generator),
) -> GetEventRecommendationsResponse:
    """Return activity recommendations tailored to the caller's preferences."""
    events = generator.generate_suggestions(
        number_events=request.number_events,
        response_preferences=request.response_preferences,
    )
    return GetEventRecommendationsResponse(events=events)

