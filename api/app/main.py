import asyncio
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncGenerator

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .schemas.events import GetEventRecommendationsRequest, GetEventRecommendationsResponse
from .routers import auth
from .services.activity_suggestion_generator import ActivitySuggestionGenerator
from .services.context_aggregator import ContextAggregator

logger = logging.getLogger(__name__)

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
    generator: ActivitySuggestionGenerator = Depends(get_activity_suggestion_generator),
) -> GetEventRecommendationsResponse:
    """Return activity recommendations tailored to the caller's preferences."""
    events = generator.generate_suggestions(
        number_events=request.number_events,
        response_preferences=request.response_preferences,
    )
    return GetEventRecommendationsResponse(events=events)


async def event_stream_generator(
    request: GetEventRecommendationsRequest,
    aggregator: ContextAggregator,
    generator: ActivitySuggestionGenerator,
) -> AsyncGenerator[str, None]:
    """Generate Server-Sent Events for event recommendation progress."""

    def send_event(event_type: str, data: dict) -> str:
        """Format a Server-Sent Event."""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    start_time = time.perf_counter()
    logger.info(
        "stream: request started",
        extra={
            "event": {
                "number_events": request.number_events,
                "response_preferences": request.response_preferences,
            }
        },
    )

    try:
        # Send initial progress event
        yield send_event("progress", {
            "status": "started",
            "message": "Starting event search...",
            "progress": 0
        })

        # Stream context gathering with progress updates
        gathered_context = None
        context_start = time.perf_counter()
        async for progress_event in aggregator.gather_context_streaming(
            response_preferences=request.response_preferences
        ):
            log_payload = dict(progress_event)
            # Capture the context from the final progress event (internal use only)
            if "_context" in progress_event:
                gathered_context = progress_event.pop("_context")  # Remove before sending to client
                context_duration = time.perf_counter() - context_start
                logger.info(
                    "stream: context gathered",
                    extra={
                        "event": {
                            "preferences": gathered_context.get("preferences"),
                            "festival_events": len(gathered_context.get("festival_events", {}).get("events", [])),
                            "eventbrite_events": len(gathered_context.get("eventbrite_events", [])),
                            "duration_seconds": round(context_duration, 3),
                        }
                    },
                )
                log_payload.pop("_context", None)

            logger.debug("stream: progress update", extra={"event": log_payload})

            # Send progress update to client (without the internal context data)
            yield send_event("progress", progress_event)
            # Small delay to ensure events are properly sent
            await asyncio.sleep(0.01)

        # Generate suggestions with intermediate progress updates
        yield send_event("progress", {
            "status": "generating",
            "message": "Analyzing your preferences...",
            "progress": 60
        })

        # Run the generator in a thread pool with progress updates
        loop = asyncio.get_running_loop()

        executor = ThreadPoolExecutor(max_workers=1)
        llm_start = time.perf_counter()
        future = executor.submit(
            generator.generate_suggestions,
            request.number_events,
            request.response_preferences,
            gathered_context,
        )
        logger.info(
            "stream: LLM generation started",
            extra={"event": {"number_events": request.number_events}},
        )

        # Send progress updates while waiting for LLM (60-95%)
        progress_steps = [
            (65, "Understanding context..."),
            (70, "Reviewing available events..."),
            (75, "Filtering relevant activities..."),
            (80, "Matching preferences to events..."),
            (85, "Scoring event matches..."),
            (90, "Ranking recommendations..."),
            (95, "Finalizing suggestions..."),
        ]

        step_index = 0
        last_update_time = time.perf_counter()
        update_interval = 2.0  # Send update every 2 seconds

        while not future.done():
            await asyncio.sleep(0.2)  # Check frequently

            current_time = time.perf_counter()
            time_since_last_update = current_time - last_update_time

            # Send next progress update if enough time has passed
            if step_index < len(progress_steps) and time_since_last_update >= update_interval:
                progress_value, progress_msg = progress_steps[step_index]
                yield send_event("progress", {
                    "status": "generating",
                    "message": progress_msg,
                    "progress": progress_value
                })
                logger.info(
                    "stream: LLM progress step",
                    extra={"event": {"progress": progress_value, "message": progress_msg}},
                )
                step_index += 1
                last_update_time = current_time

        # Send any remaining progress steps that weren't sent
        while step_index < len(progress_steps):
            progress_value, progress_msg = progress_steps[step_index]
            yield send_event("progress", {
                "status": "generating",
                "message": progress_msg,
                "progress": progress_value
            })
            logger.info(
                "stream: LLM progress step (fast completion)",
                extra={"event": {"progress": progress_value, "message": progress_msg}},
            )
            step_index += 1
            await asyncio.sleep(0.3)  # Small delay so user can see the progress

        # Get the result
        events = future.result()
        executor.shutdown(wait=False)
        llm_duration = time.perf_counter() - llm_start
        logger.info(
            "stream: LLM generation completed",
            extra={
                "event": {
                    "event_count": len(events),
                    "duration_seconds": round(llm_duration, 3),
                }
            },
        )

        # Send serialization progress update
        yield send_event("progress", {
            "status": "generating",
            "message": "Preparing results...",
            "progress": 96
        })

        # Send final result - convert Location objects to [x, y] tuples for JSON serialization
        serialized_events = []
        serialization_start = time.perf_counter()
        for event in events:
            try:
                # Serialize using pydantic (v2 uses model_dump, v1 uses dict)
                if hasattr(event, 'model_dump'):
                    event_dict = event.model_dump()
                elif hasattr(event, 'dict'):
                    event_dict = event.dict()
                else:
                    # Fallback for plain dicts
                    event_dict = dict(event)

                # Convert Location object to tuple format expected by frontend [x, y]
                location = event_dict.get('location')
                if isinstance(location, dict) and 'x' in location and 'y' in location:
                    event_dict['location'] = [location['x'], location['y']]
                elif hasattr(location, 'x') and hasattr(location, 'y'):
                    event_dict['location'] = [location.x, location.y]

                serialized_events.append(event_dict)
            except Exception as e:
                logger.error("Failed to serialize event", extra={"event": {"error": str(e)}})
                raise

        serialization_duration = time.perf_counter() - serialization_start
        total_duration = time.perf_counter() - start_time
        logger.info(
            "stream: serialization completed",
            extra={
                "event": {
                    "serialized_count": len(serialized_events),
                    "serialization_seconds": round(serialization_duration, 3),
                    "total_seconds": round(total_duration, 3),
                }
            },
        )

        # Send packaging progress
        yield send_event("progress", {
            "status": "generating",
            "message": "Packaging recommendations...",
            "progress": 98
        })

        yield send_event("complete", {
            "status": "complete",
            "message": "Recommendations ready!",
            "progress": 100,
            "events": serialized_events
        })

    except Exception as e:
        logger.exception("Error in streaming recommendations")
        yield send_event("error", {
            "status": "error",
            "message": f"Error generating recommendations: {str(e)}"
        })


@app.post(
    "/events/recommendations/stream",
    summary="Stream activity recommendations with progress updates",
)
async def stream_event_recommendations(
    request: GetEventRecommendationsRequest,
    aggregator: ContextAggregator = Depends(get_context_aggregator),
    generator: ActivitySuggestionGenerator = Depends(get_activity_suggestion_generator),
):
    """Stream activity recommendations with real-time progress updates using Server-Sent Events."""
    return StreamingResponse(
        event_stream_generator(request, aggregator, generator),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering for nginx
        },
    )
