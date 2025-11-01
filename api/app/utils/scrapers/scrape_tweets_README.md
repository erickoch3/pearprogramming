# X (Twitter) Activity Scraper

A Python script that uses the X (Twitter) API v2 to fetch recent tweets about activities and events in Edinburgh.

## Requirements

- Python 3.x
- `requests`
- `python-dotenv`

Install dependencies:
```bash
pip install requests python-dotenv
```

## Setup

1. Create a `.env` file in the `api` directory (parent of `app/services`)

2. Add your X API Bearer Token:
```
X_API_KEY=your_bearer_token_here
```

To get a Bearer Token:
1. Sign up for a Twitter Developer account at https://developer.twitter.com/
2. Create an app and generate a Bearer Token
3. Add it to your `.env` file

## Usage

```bash
python scrape_tweets.py [OPTIONS]
```

### Command-Line Arguments

- `--limit` (default: `10`)
  - Number of tweets to fetch

### Examples

```bash
# Fetch 10 tweets (default)
python scrape_tweets.py

# Fetch 50 tweets
python scrape_tweets.py --limit 50
```

## What It Searches For

The script searches for tweets containing:
- **Activity keywords**: event, festival, concert, show, comedy, market, food market, brunch, dinner, exhibition, museum, gallery, workshop, meetup, hike, walk, running, park, tour, popup
- **Location terms**: edinburgh, leith, portobello, royal mile, stockbridge, princes street, edinburgh old town, edinburgh new town

It filters to:
- English language tweets
- Excludes retweets

## Output

The script outputs:
1. **Console**: Prints tweets as they're fetched with username, text, and URL
2. **JSON file**: Saves all tweets to `tweets.json` in the same directory

Each tweet includes:
- `tweet_id`: Unique tweet ID
- `username`: Twitter username
- `text`: Tweet text
- `url`: Direct link to the tweet
- `created_at`: Timestamp when the tweet was created
- `like_count`: Number of likes
- `retweet_count`: Number of retweets
- `reply_count`: Number of replies

## Error Handling

The script includes enhanced error handling for:
- **Rate limiting** (HTTP 429): Shows wait time and remaining requests
- **API errors**: Displays detailed error messages from the X API
- **Authentication errors**: Clearly indicates if API key is missing or invalid

## Notes

- The X API v2 has query length limits (512 characters) - the script validates this
- Rate limits apply based on your Twitter Developer account tier
- The script respects rate limits and shows helpful messages when exceeded

