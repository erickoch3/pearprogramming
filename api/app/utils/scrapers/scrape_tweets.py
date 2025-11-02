#!/usr/bin/env python3
"""Scrape tweets from X API and store them in the database."""

import os
import re
import sys
import argparse
import requests
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from dotenv import load_dotenv

script_dir = Path(__file__).resolve().parent
app_dir = script_dir.parent.parent

try:  # Preferred path when imported as part of the app package
    from ...core.database import SessionLocal, engine, Base
    from ...models.tweet import Tweet
except ImportError:  # Fallback for running as a standalone script
    sys.path.insert(0, str(app_dir))
    from app.core.database import SessionLocal, engine, Base
    from app.models.tweet import Tweet

from sqlalchemy import or_

# Load .env file from the root directory
env_path = app_dir.parent / ".env"
load_dotenv(dotenv_path=env_path)

API_URL = "https://api.x.com/2/tweets/search/recent"

def _require_api_key() -> str:
    """Return the configured X API key or raise a helpful error."""
    api_key = os.getenv("X_API_KEY")
    if not api_key:
        raise ValueError("Please set the X_API_KEY environment variable.")
    return api_key

# Keywords that tend to indicate real-world activities
# Prioritized list kept under query length limit (512 chars)
# Multi-word terms are stored without quotes - will be quoted in build_query()
ACTIVITY_KEYWORDS = [
    "event", "festival", "concert", "show",
    "comedy", "market", "food market", "brunch", "dinner",
    "exhibition", "museum", "gallery", "workshop", "meetup",
    "hike", "walk", "running",
    "park", "tour", "popup"
]

# Edinburgh locality cues to reduce false positives elsewhere in GB
# Simplified list to keep query under 512 character limit
# Multi-word terms are stored without quotes - will be quoted in build_query()
LOCATION_TERMS = [
    "edinburgh", "leith", "portobello", "royal mile", "stockbridge",
    "princes street", "edinburgh old town", "edinburgh new town"
]


def _sanitize_term(term: str) -> str:
    return re.sub(r"\s+", " ", term.strip())


def _quote_term(term: str) -> str:
    sanitized = _sanitize_term(term)
    if not sanitized:
        return ""
    sanitized = sanitized.replace('"', '\\"')
    if " " in sanitized:
        return f'"{sanitized}"'
    return sanitized


def _compose_query_from_terms(keyword_terms: Iterable[str], location_terms: Iterable[str]) -> str:
    kw_list = [term for term in keyword_terms if term]
    loc_list = [term for term in location_terms if term]
    kw_clause = f"({' OR '.join(kw_list)})" if kw_list else ""
    loc_clause = f"({' OR '.join(loc_list)})" if loc_list else ""
    parts = [kw_clause, loc_clause, "-is:retweet", "lang:en"]
    return " ".join(part for part in parts if part).strip()


def _trim_terms_to_limit(keyword_terms: List[str], location_terms: List[str]) -> List[str]:
    trimmed: List[str] = []
    for term in keyword_terms:
        candidate = trimmed + [term]
        query = _compose_query_from_terms(candidate, location_terms)
        if len(query) <= 512:
            trimmed.append(term)
        else:
            break
    if not trimmed and keyword_terms:
        trimmed = keyword_terms[:1]
    return trimmed


def build_query(activity_keywords=None, location_terms=None):
    """
    Build a properly formatted query for X API v2.
    Multi-word terms are quoted to ensure proper parsing.

    Args:
        activity_keywords: Optional list of activity keywords. If None, uses default ACTIVITY_KEYWORDS
        location_terms: Optional list of location terms. If None, uses default LOCATION_TERMS
    """

    kw_list = activity_keywords if activity_keywords is not None else ACTIVITY_KEYWORDS
    loc_list = location_terms if location_terms is not None else LOCATION_TERMS

    kw_terms = [_quote_term(kw) for kw in kw_list if kw]
    loc_terms = [_quote_term(loc) for loc in loc_list if loc]

    kw_terms = _trim_terms_to_limit(kw_terms, loc_terms)
    return _compose_query_from_terms(kw_terms, loc_terms)


def build_event_query(event_title: str, extra_keywords: Optional[Iterable[str]] = None, location_terms=None) -> str:
    """Build a query that focuses on a specific event title."""

    loc_list = location_terms if location_terms is not None else LOCATION_TERMS
    loc_terms = [_quote_term(loc) for loc in loc_list if loc]

    keyword_candidates: List[str] = []

    if event_title:
        title_clean = _sanitize_term(event_title)
        if title_clean:
            keyword_candidates.append(_quote_term(title_clean))

            words = [w for w in re.split(r"[^\w#]+", title_clean) if len(w) > 2]
            keyword_candidates.extend(_quote_term(w) for w in words[:5])

            bigrams = [" ".join(words[i:i + 2]) for i in range(len(words) - 1)]
            keyword_candidates.extend(_quote_term(bg) for bg in bigrams[:3])

    if extra_keywords:
        keyword_candidates.extend(_quote_term(term) for term in extra_keywords if term)

    keyword_candidates.extend(_quote_term(term) for term in ACTIVITY_KEYWORDS[:5])

    # De-duplicate while preserving order
    seen = set()
    ordered_terms: List[str] = []
    for term in keyword_candidates:
        if term and term not in seen:
            seen.add(term)
            ordered_terms.append(term)

    if not ordered_terms:
        ordered_terms = [_quote_term(event_title or "edinburgh events")]

    ordered_terms = _trim_terms_to_limit(ordered_terms, loc_terms)
    return _compose_query_from_terms(ordered_terms, loc_terms)


def fetch_page(api_key, query, next_token=None, max_results=10):
    """Fetch a page of tweets from the X API."""
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "query": query,
        "max_results": max_results,  # default: 10 tweets
        "tweet.fields": "created_at,public_metrics,geo,lang,entities",
        "expansions": "author_id,geo.place_id",
        "user.fields": "username,verified,location",
        "place.fields": "full_name,id,geo,name,place_type"
    }
    if next_token:
        params["next_token"] = next_token
    r = requests.get(API_URL, headers=headers, params=params, timeout=30)

    # Enhanced error handling to show actual API error response
    if not r.ok:
        error_msg = f"API Error {r.status_code}: {r.reason}"

        # Check for rate limit information in headers
        if r.status_code == 429:
            retry_after = r.headers.get('Retry-After')
            rate_limit_remaining = r.headers.get('x-rate-limit-remaining')
            rate_limit_reset = r.headers.get('x-rate-limit-reset')

            if retry_after:
                error_msg += f"\n Rate limit exceeded. Please wait {retry_after} seconds before retrying."
            elif rate_limit_reset:
                reset_time = int(rate_limit_reset)
                current_time = int(time.time())
                wait_seconds = reset_time - current_time
                if wait_seconds > 0:
                    error_msg += f"\n Rate limit will reset in {wait_seconds} seconds (at {reset_time})."
                else:
                    error_msg += f"\n Rate limit reset time: {reset_time}"

            if rate_limit_remaining:
                error_msg += f"\n Requests remaining: {rate_limit_remaining}"
            else:
                error_msg += "\n Rate limit exceeded. Please wait a few minutes before retrying."

        try:
            error_data = r.json()
            if "errors" in error_data:
                error_details = "; ".join([f"{e.get('message', 'Unknown error')} (code: {e.get('code', 'N/A')})"
                                          for e in error_data["errors"]])
                error_msg += f"\nDetails: {error_details}"
            elif "detail" in error_data:
                error_msg += f"\nDetails: {error_data['detail']}"
            else:
                error_msg += f"\nResponse: {error_data}"
        except ValueError:
            error_msg += f"\nResponse text: {r.text[:500]}"
        raise requests.exceptions.HTTPError(error_msg)

    r.raise_for_status()
    return r.json()


def parse_tweet_datetime(date_string):
    """Parse X API datetime string to Python datetime object."""
    if not date_string:
        return None
    try:
        # X API returns ISO 8601 format: 2024-01-01T12:00:00.000Z
        return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    except (ValueError, AttributeError):
        return None


def index_users(includes):
    """Index users by their ID for quick lookup."""
    users = {}
    for u in includes.get("users", []):
        users[u["id"]] = u
    return users


def _format_tweet_record(tweet_data, users):
    """Convert raw tweet payload into a serializable record."""
    if not tweet_data:
        return None

    tweet_id = tweet_data.get("id")
    if tweet_id is None:
        return None

    try:
        record_id = int(tweet_id)
    except (TypeError, ValueError):  # pragma: no cover - defensive fallback
        record_id = abs(hash(tweet_id))

    uid = tweet_data.get("author_id")
    user = users.get(uid, {}) if users else {}
    username = user.get("username", "unknown")

    text = tweet_data.get("text", "") or ""
    text = text.replace("\n", " ")

    created_at = parse_tweet_datetime(tweet_data.get("created_at"))
    metrics = tweet_data.get("public_metrics", {}) or {}
    
    # Generate tweet URL
    url = None
    if username and username != "unknown" and tweet_id:
        url = f"https://x.com/{username}/status/{tweet_id}"

    return {
        "id": record_id,
        "text": text,
        "username": username,
        "url": url,
        "like_count": metrics.get("like_count", 0) or 0,
        "retweet_count": metrics.get("retweet_count", 0) or 0,
        "created_at": created_at,
        "scraped_at": datetime.now(timezone.utc),
        "is_synthetic": False,
    }


def _ensure_event_reference(payload: dict, event_title: Optional[str]) -> dict:
    if not event_title:
        return payload

    title_clean = event_title.strip()
    if not title_clean:
        return payload

    text_lower = payload["text"].lower() if payload["text"] else ""
    if title_clean.lower() not in text_lower:
        payload["text"] = f"{payload['text']} • Related to {title_clean}".strip()

    return payload


def write_tweets_to_db(limit=10, activity_keywords=None, location_terms=None):

    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)

    api_key = _require_api_key()
    query = build_query(activity_keywords=activity_keywords, location_terms=location_terms)

    # Validate query length (X API v2 has a 512 character limit)
    query_length = len(query)
    if query_length > 512:
        print(f"⚠️  Warning: Query length ({query_length} chars) exceeds X API limit (512 chars)")
        print(f"Query preview: {query[:100]}...")
        print("Attempting to send anyway, but may fail.\n")
    else:
        print(f"✓ Query length: {query_length} characters (limit: 512)\n")

    total = 0
    stored = 0
    next_token = None
    seen = set()

    print(f"🔍 Searching for up to {limit} tweets about activities in Edinburgh...\n")

    # Create database session
    db = SessionLocal()

    try:
        while total < limit:
            remaining = min(10, limit - total)
            data = fetch_page(
                api_key, query, next_token=next_token, max_results=remaining
            )
            includes = data.get("includes", {})
            users = index_users(includes)

            for t in data.get("data", []):
                tweet_id = t.get("id")
                if tweet_id in seen:
                    continue

                payload = _format_tweet_record(t, users)
                if payload is None:
                    continue

                seen.add(tweet_id)

                tweet = Tweet(
                    text=payload["text"],
                    like_count=payload["like_count"],
                    retweet_count=payload["retweet_count"],
                    created_at=payload["created_at"],
                    scraped_at=payload["scraped_at"],
                    username=payload.get("username"),
                    url=payload.get("url"),
                    is_synthetic=payload.get("is_synthetic", False),
                )

                db.add(tweet)
                stored += 1

                print(
                    f"@{payload['username']}: {payload['text']}\n→ {payload.get('url', 'N/A')}\n"
                )
                total += 1

                if total >= limit:
                    break

            # Commit after each page
            db.commit()

            next_token = data.get("meta", {}).get("next_token")
            if not next_token:
                break

        print(f"Done — fetched {total} tweets, stored {stored} in database.\n")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


def search_tweets_for_event(event_title: str, extra_keywords: Optional[Iterable[str]] = None, *, limit: int = 10, location_terms=None) -> List[dict]:
    """Fetch tweets related to a specific event without persisting them.

    Returns only real tweets from the X API. If the API key is missing, the
    request fails, or no tweets match the query, the result may contain fewer
    tweets than requested (including zero).
    """

    if not event_title:
        return []

    collected: List[dict] = []
    remaining = max(0, limit)
    
    # Try to fetch real tweets if API key is available
    try:
        api_key = _require_api_key()
        query = build_event_query(event_title, extra_keywords=extra_keywords, location_terms=location_terms)

        seen_ids = set()
        next_token = None

        while remaining > 0:
            page_limit = min(remaining, 10)
            data = fetch_page(api_key, query, next_token=next_token, max_results=page_limit)
            includes = data.get("includes", {})
            users = index_users(includes)

            for raw_tweet in data.get("data", []):
                tweet_id = raw_tweet.get("id")
                if tweet_id in seen_ids:
                    continue

                payload = _format_tweet_record(raw_tweet, users)
                if payload is None:
                    continue

                seen_ids.add(tweet_id)
                collected.append(_ensure_event_reference(payload, event_title))
                remaining -= 1

                if remaining <= 0:
                    break

            next_token = data.get("meta", {}).get("next_token")
            if not next_token:
                break
                
    except (ValueError, Exception):
        # API key not set or request failed - return any tweets collected so far
        pass

    return collected


def get_last_scrape_time():
    """Get the timestamp of the most recent tweet scrape."""
    db = SessionLocal()
    try:
        # Get the most recent scraped_at timestamp
        most_recent = db.query(Tweet).order_by(Tweet.scraped_at.desc()).first()
        return most_recent.scraped_at if most_recent else None
    finally:
        db.close()


def get_tweets(limit=10, threshold_hours_for_refresh=2, activity_keywords=None, location_terms=None, filter_keywords=None):
    """
    Get events (tweets) from the database.

    If the last scrape was more than threshold_hours_for_refresh ago, fetch new tweets first.

    Args:
        limit: Number of tweets to return (default: 10)
        threshold_hours_for_refresh: Number of hours before data is considered stale (default: 2)
        activity_keywords: Optional list of activity keywords to use for scraping
        location_terms: Optional list of location terms to use for scraping
        filter_keywords: Optional list of keywords to filter returned tweets (doesn't affect scraping)

    Returns:
        List of Tweet objects
    """
    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # Check if we need to refresh the data
    last_scrape = get_last_scrape_time()
    needs_refresh = False

    if last_scrape is None:
        print("No tweets in database. Fetching new tweets...")
        needs_refresh = True
    else:
        # Calculate time since last scrape
        now = datetime.now(timezone.utc)
        # Handle both timezone-aware and naive datetimes
        if last_scrape.tzinfo is None:
            last_scrape = last_scrape.replace(tzinfo=timezone.utc)
        time_since_scrape = now - last_scrape
        hours_since_scrape = time_since_scrape.total_seconds() / 3600

        if hours_since_scrape > threshold_hours_for_refresh:
            print(f"Last scrape was {hours_since_scrape:.1f} hours ago (threshold: {threshold_hours_for_refresh} hours). Fetching new tweets...")
            needs_refresh = True

    # Refresh data if needed
    if needs_refresh:
        write_tweets_to_db(limit, activity_keywords=activity_keywords, location_terms=location_terms)

    # Fetch and return tweets from database
    db = SessionLocal()
    try:
        query = db.query(Tweet)
        
        # Filter by keywords if provided
        if filter_keywords:
            # Create a filter that matches if tweet text contains any of the keywords
            keyword_filters = [Tweet.text.ilike(f'%{kw}%') for kw in filter_keywords]
            query = query.filter(or_(*keyword_filters))
        
        tweets = query.order_by(Tweet.scraped_at.desc()).limit(limit).all()
        return tweets
    finally:
        db.close()


def main():
    """Main function to scrape tweets and store in database."""
    parser = argparse.ArgumentParser(description="Fetch recent X tweets about activities in Edinburgh and store in database.")
    parser.add_argument("--limit", type=int, default=10, help="Number of tweets to fetch (default: 10).")
    args = parser.parse_args()
    write_tweets_to_db(args.limit, activity_keywords=None, location_terms=None)

if __name__ == "__main__":
    main()
