# Eventbrite Web Scraper

A Python script that scrapes Eventbrite's public website to fetch events by location. Since Eventbrite's public search API was deprecated in February 2020, this script uses web scraping as an alternative.

## Requirements

- Python 3.x
- `requests`
- `beautifulsoup4`
- `lxml`
- `python-dateutil`
- `pytz`
- `python-dotenv`

Install dependencies:
```bash
pip install requests beautifulsoup4 lxml python-dateutil pytz python-dotenv
```

## Setup

1. Get a Google Maps API Key:
   - Go to https://console.cloud.google.com/
   - Create a project or select an existing one
   - Enable the Geocoding API
   - Create credentials (API Key)
   - Copy your API key

2. Set the API key as an environment variable:
   ```bash
   export GOOGLE_MAPS_API_KEY=your_api_key_here
   ```
   
   Or create a `.env` file in the `api` directory:
   ```
   GOOGLE_MAPS_API_KEY=your_api_key_here
   ```

## Usage

```bash
python scrape_eventbrite.py [OPTIONS]
```

### Command-Line Arguments

- `--location` (default: `"Edinburgh, United Kingdom"`)
  - Search location (e.g., "London, United Kingdom", "New York, United States")
  
- `--pages` (default: `3`)
  - Maximum number of pages to fetch
  
- `--per_page` (default: `50`)
  - Maximum results per page
  
- `--sleep` (default: `1.0`)
  - Delay between paginated requests in seconds (for respectful scraping)
  
- `--out` (default: `events_edinburgh_eventbrite_scraper.json`)
  - Output JSON file path
  
- `--debug`
  - Enable debug mode (shows detailed diagnostic information)
  
- `--api-key`
  - Google Maps API key (optional if `GOOGLE_MAPS_API_KEY` environment variable is set)

### Examples

```bash
# Basic usage with defaults
python scrape_eventbrite.py

# Search for events in London
python scrape_eventbrite.py --location "London, United Kingdom"

# Fetch more pages with debug output
python scrape_eventbrite.py --pages 5 --debug

# Custom output file
python scrape_eventbrite.py --out my_events.json
```

## Output

The script outputs a JSON file containing an array of event objects. Each event includes:
- `location_name`: Venue address/name (string)
- `activity_name`: Event name (string)
- `latitude`: Latitude coordinate from Google Maps API (float)
- `longitude`: Longitude coordinate from Google Maps API (float)
- `time`: Event datetime in ISO 8601 format (string, in UK timezone)
- `url`: Event URL (string, optional - only included if exists)
- `description`: Event description (string, optional - only included if exists and non-empty)

**Note:** Events are automatically skipped if:
- The venue address is invalid or empty
- Geocoding fails (address cannot be found on Google Maps)
- No Google Maps API key is provided

A preview of the first 5 events is also printed to stdout.

## Important Notes

⚠️ **Please respect Eventbrite's robots.txt and terms of service.**
- The script includes built-in delays between requests
- Uses proper user agents to identify as a bot
- Do not run too frequently to avoid overloading their servers

