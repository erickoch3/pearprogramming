from fastapi import Depends, FastAPI, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List

from .schemas.events import GetEventRecommendationsRequest, GetEventRecommendationsResponse
from .schemas.tweets import Tweet, TweetList
from .routers import auth
from .services.activity_suggestion_generator import ActivitySuggestionGenerator
from .services.context_aggregator import ContextAggregator
from .utils.keyword_extractor import extract_keywords_from_events
from .utils.scrapers.scrape_tweets import search_tweets_for_event, write_tweets_to_db

app = FastAPI(title="Pear Programming API", version="0.1.0")

# Allow browser clients (e.g., Next.js dev server) to call the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    response_model_exclude_none=True,
    summary="Generate activity recommendations",
)
async def get_event_recommendations(
    request: GetEventRecommendationsRequest,
    background_tasks: BackgroundTasks,
    generator: ActivitySuggestionGenerator = Depends(get_activity_suggestion_generator),
) -> GetEventRecommendationsResponse:
    """Return activity recommendations tailored to the caller's preferences."""
    events = generator.generate_suggestions(
        number_events=request.number_events,
        response_preferences=request.response_preferences,
    )
    
    # Automatically extract keywords from events and scrape tweets in background
    # Wrap in try-except to ensure any errors don't affect the main response
    if events:
        try:
            keywords = extract_keywords_from_events(events, max_keywords=30)
            if keywords:
                # Create a safe wrapper function that handles exceptions internally
                def safe_scrape_tweets():
                    try:
                        write_tweets_to_db(
                            limit=20,
                            activity_keywords=keywords,
                            location_terms=None  # Use default location terms
                        )
                    except Exception as scrape_error:
                        # Silently fail in background - logging can be added if needed
                        import logging
                        logging.getLogger(__name__).debug(
                            f"Background tweet scraping failed: {scrape_error}"
                        )
                
                # Trigger tweet scraping in background (non-blocking)
                background_tasks.add_task(safe_scrape_tweets)
        except Exception as e:
            # Log error but don't fail the request
            import logging
            logging.getLogger(__name__).warning(f"Failed to extract keywords or schedule tweet scraping: {e}")
    
    return GetEventRecommendationsResponse(events=events)


@app.get(
    "/tweets",
    response_model=TweetList,
    response_model_exclude_none=True,
    summary="Get tweets for events",
)
async def get_tweets(
    limit: int = Query(default=10, ge=1, le=50, description="Number of tweets to return"),
    keywords: Optional[str] = Query(default=None, description="Comma-separated keywords to filter tweets"),
    event_title: Optional[str] = Query(default=None, description="Event title to search tweets for"),
) -> TweetList:
    """Retrieve tweets from the database or fetch live tweets for a specific event."""
    from .utils.scrapers.scrape_tweets import get_tweets as get_tweets_from_db

    filter_keywords = [kw.strip() for kw in keywords.split(",") if kw.strip()] if keywords else None

    if event_title:
        live_tweets = search_tweets_for_event(
            event_title,
            extra_keywords=filter_keywords,
            limit=limit,
        )
        return TweetList(tweets=[Tweet.model_validate(tweet) for tweet in live_tweets])

    tweets = get_tweets_from_db(
        limit=limit,
        threshold_hours_for_refresh=2,
        filter_keywords=filter_keywords,
    )

    return TweetList(tweets=[Tweet.model_validate(tweet) for tweet in tweets])
