#!/usr/bin/env python3
"""Scrape tweets from X API and store them in the database."""

import os
import sys
import argparse
import requests
import time
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path to enable imports
script_dir = Path(__file__).resolve().parent
api_dir = script_dir.parent.parent
sys.path.insert(0, str(api_dir))

from app.core.database import SessionLocal, engine, Base
from app.models.tweet import Tweet

# Load .env file from the root directory
env_path = api_dir.parent / ".env"
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


def build_query():
    """
    Build a properly formatted query for X API v2.
    Multi-word terms are quoted to ensure proper parsing.
    """
    def quote_term(term):
        """Quote terms that contain spaces."""
        if " " in term:
            return f'"{term}"'
        return term

    kw_terms = [quote_term(kw) for kw in ACTIVITY_KEYWORDS]
    loc_terms = [quote_term(loc) for loc in LOCATION_TERMS]

    kw = "(" + " OR ".join(kw_terms) + ")"
    loc = "(" + " OR ".join(loc_terms) + ")"
    # -is:retweet removes RTs, lang:en keeps it readable
    # Note: place_country operator is not available in basic/free tier, so we rely on location keywords
    query = f"{kw} {loc} -is:retweet lang:en"
    return query


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


def write_tweets_to_db(limit=10):

    # Create database tables if they don't exist
    Base.metadata.create_all(bind=engine)

    api_key = _require_api_key()
    query = build_query()

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
                if t["id"] in seen:
                    continue
                seen.add(t["id"])

                uid = t.get("author_id")
                user = users.get(uid, {})
                username = user.get("username", "unknown")
                url = f"https://x.com/{username}/status/{t['id']}"
                text = t.get("text", "").replace("\n", " ")

                # Parse tweet data
                created_at = parse_tweet_datetime(t.get("created_at"))
                metrics = t.get("public_metrics", {})
                like_count = metrics.get("like_count", 0)
                retweet_count = metrics.get("retweet_count", 0)

                # Create and store tweet in database
                tweet = Tweet(
                    text=text,
                    like_count=like_count,
                    retweet_count=retweet_count,
                    created_at=created_at,
                    scraped_at=datetime.now(timezone.utc)
                )

                db.add(tweet)
                stored += 1

                print(f"@{username}: {text}\n→ {url}\n")
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

def get_last_scrape_time():
    """Get the timestamp of the most recent tweet scrape."""
    db = SessionLocal()
    try:
        # Get the most recent scraped_at timestamp
        most_recent = db.query(Tweet).order_by(Tweet.scraped_at.desc()).first()
        return most_recent.scraped_at if most_recent else None
    finally:
        db.close()


def get_tweets(limit=10, threshold_hours_for_refresh=2):
    """
    Get events (tweets) from the database.

    If the last scrape was more than threshold_hours_for_refresh ago, fetch new tweets first.

    Args:
        limit: Number of tweets to return (default: 10)
        threshold_hours_for_refresh: Number of hours before data is considered stale (default: 2)

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
        write_tweets_to_db(limit)

    # Fetch and return tweets from database
    db = SessionLocal()
    try:
        tweets = db.query(Tweet).order_by(Tweet.scraped_at.desc()).limit(limit).all()
        return tweets
    finally:
        db.close()


def main():
    """Main function to scrape tweets and store in database."""
    parser = argparse.ArgumentParser(description="Fetch recent X tweets about activities in Edinburgh and store in database.")
    parser.add_argument("--limit", type=int, default=10, help="Number of tweets to fetch (default: 10).")
    args = parser.parse_args()
    write_tweets_to_db(args.limit)

if __name__ == "__main__":
    main()
