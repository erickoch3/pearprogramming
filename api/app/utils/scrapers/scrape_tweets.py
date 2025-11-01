#!/usr/bin/env python3
import os, csv, argparse, requests, sys, time, json
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the api directory (parent of app/services)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

API_URL = "https://api.x.com/2/tweets/search/recent"

# --- Load API key from environment ---
API_KEY = os.getenv("X_API_KEY")
if not API_KEY:
    raise ValueError("Please set the X_API_KEY environment variable.")
# -------------------------------------

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
    "edinburgh", "leith", "portobello", "royal mile", "stockbridge","princes street","edinburgh old town","edinburgh new town"
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

def index_users(includes):
    users = {}
    for u in includes.get("users", []):
        users[u["id"]] = u
    return users

def main():
    parser = argparse.ArgumentParser(description="Fetch recent X tweets about activities in Edinburgh.")
    parser.add_argument("--limit", type=int, default=10, help="Number of tweets to fetch (default: 10).")
    args = parser.parse_args()
    
    # Fixed output file name
    output_file = "tweets.json"

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
    next_token = None
    seen = set()
    tweets_data = []  # Store tweets for CSV export

    print(f"🔍 Searching for up to {args.limit} tweets about activities in Edinburgh...\n")

    while total < args.limit:
        remaining = min(10, args.limit - total)
        data = fetch_page(API_KEY, query, next_token=next_token, max_results=remaining)
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
            
            # Store tweet data
            tweets_data.append({
                "tweet_id": t["id"],
                "username": username,
                "text": text,
                "url": url,
                "created_at": t.get("created_at", ""),
                "like_count": t.get("public_metrics", {}).get("like_count", 0),
                "retweet_count": t.get("public_metrics", {}).get("retweet_count", 0),
                "reply_count": t.get("public_metrics", {}).get("reply_count", 0),
            })
            
            print(f"@{username}: {text}\n→ {url}\n")
            total += 1
            if total >= args.limit:
                break

        next_token = data.get("meta", {}).get("next_token")
        if not next_token:
            break

    # Save tweets to JSON file
    output_path = Path(output_file)
    if tweets_data:
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(tweets_data, jsonfile, indent=2, ensure_ascii=False)
        print(f"Done — fetched {total} tweets.")
        print(f"Saved to: {output_path.absolute()}\n")
    else:
        print(f"Done — fetched {total} tweets.\n")

if __name__ == "__main__":
    main()
