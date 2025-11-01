# Eventbrite Web Scraper

A Python script that scrapes Eventbrite's public website to fetch events by location. Since Eventbrite's public search API was deprecated in February 2020, this script uses web scraping as an alternative.

## Requirements

- Python 3.x
- `requests`
- `beautifulsoup4`
- `lxml`

Install dependencies:
```bash
pip install requests beautifulsoup4 lxml
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
- `id`: Event ID
- `name`: Event name
- `description`: Event description (usually empty on listing pages)
- `start`: Start date/time
- `url`: Event URL
- `status`: Event status (typically "live")
- `is_free`: Whether the event is free
- `currency`: Currency code
- `logo`: Event image/logo URL
- `venue`: Venue information (name, address)
- `source`: Always "eventbrite_web_scraper"

A preview of the first 5 events is also printed to stdout.

## Important Notes

⚠️ **Please respect Eventbrite's robots.txt and terms of service.**
- The script includes built-in delays between requests
- Uses proper user agents to identify as a bot
- Do not run too frequently to avoid overloading their servers

