#!/usr/bin/env python3
"""
Eventbrite Web Scraper

This script scrapes Eventbrite's public website to fetch events by location.
The Eventbrite API public search endpoint was deprecated in February 2020, so
we use web scraping as an alternative.

IMPORTANT: Always respect Eventbrite's robots.txt and terms of service.
This scraper includes delays and proper user agents to be respectful.

References:
- https://rollout.com/integration-guides/eventbrite/api-essentials
- https://www.eventbrite.com/platform/docs/introduction
"""
import argparse, requests, sys, time, json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import os
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import pytz
from dotenv import load_dotenv

def build_search_url(location: str, page: int = 1):
    """Build Eventbrite search URL from location."""
    # Parse location (e.g., "Edinburgh, United Kingdom")
    location_parts = [part.strip() for part in location.split(",")]
    city = location_parts[0].lower().replace(" ", "-")
    country = location_parts[-1].lower().replace(" ", "-") if len(location_parts) > 1 else ""
    
    # Eventbrite URL format: /d/[country]--[city]/events/ or /d/[city]/events/
    if country and country != city:
        url = f"https://www.eventbrite.com/d/{country}--{city}/events/"
    else:
        url = f"https://www.eventbrite.com/d/{city}/events/"
    
    # Add page parameter if not first page
    if page > 1:
        separator = "&" if "?" in url else "?"
        url += f"{separator}page={page}"
    
    return url

def extract_event_id_from_url(url: str):
    """Extract event ID from Eventbrite URL."""
    # Eventbrite URLs can be:
    # - https://www.eventbrite.com/e/event-name-123456789/
    # - https://www.eventbrite.co.uk/e/event-name-123456789?aff=...
    # Event ID is the number at the end before query params or trailing slash
    match = re.search(r'/e/[^/?#]+-(\d+)(?:[/?]|$)', url)
    if match:
        return match.group(1)
    return None

def geocode_address(address: str, api_key: str, location_context: str = None, debug: bool = False):
    """
    Geocode an address using Google Maps Geocoding API.
    
    Args:
        address: Address string to geocode
        api_key: Google Maps API key
        location_context: Optional location context (e.g., "Edinburgh, United Kingdom") to append for better geocoding
        debug: Enable debug output
    
    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    if not address or not address.strip():
        return None
    
    # Skip invalid addresses
    invalid_patterns = ["Check ticket price on event", ""]
    if address.strip() in invalid_patterns:
        return None
    
    # Enhance address with location context if provided
    geocode_query = address
    if location_context:
        # Only append location context if it's not already in the address
        if location_context.lower() not in address.lower():
            geocode_query = f"{address}, {location_context}"
    
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": geocode_query,
            "key": api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        status = data.get("status")
        error_message = data.get("error_message", "")
        
        if status == "OK" and data.get("results"):
            location = data["results"][0]["geometry"]["location"]
            lat = location["lat"]
            lng = location["lng"]
            
            if debug:
                print(f"Geocoded '{geocode_query}': ({lat}, {lng})", file=sys.stderr)
            
            return (lat, lng)
        elif status == "REQUEST_DENIED":
            # This is an API configuration issue - provide helpful error
            error_msg = f"Geocoding API REQUEST_DENIED for '{geocode_query}'"
            if error_message:
                error_msg += f": {error_message}"
            else:
                error_msg += ". Check: 1) API key is valid, 2) Geocoding API is enabled, 3) Billing is enabled, 4) API key restrictions allow this usage"
            
            if debug:
                print(error_msg, file=sys.stderr)
            
            # Raise a custom exception so we can catch it and provide user guidance
            raise ValueError(f"REQUEST_DENIED: {error_message}" if error_message else "REQUEST_DENIED")
        else:
            if debug:
                print(f"Geocoding failed for '{geocode_query}': {status}", file=sys.stderr)
                if error_message:
                    print(f"  Error message: {error_message}", file=sys.stderr)
            return None
            
    except ValueError:
        # Re-raise ValueError (REQUEST_DENIED) so caller can handle it
        raise
    except Exception as e:
        if debug:
            print(f"Error geocoding '{geocode_query}': {e}", file=sys.stderr)
        return None

def parse_event_datetime(date_str: str, debug: bool = False):
    """
    Parse event datetime string into a datetime object.
    
    Handles:
    - Relative dates: "Today • 9:00 PM", "Tomorrow • 11:00 AM"
    - Absolute dates: "Sat, Nov 22 • 8:00 PM", "Tue, Dec 30 • 8:00 PM"
    - Day names: "Tuesday • 6:00 PM", "Wednesday • 6:30 PM"
    
    Args:
        date_str: Date/time string from Eventbrite
        debug: Enable debug output
    
    Returns:
        datetime object in UK timezone or None if parsing fails
    """
    if not date_str or not date_str.strip():
        return None
    
    # Get current time in UK timezone
    uk_tz = pytz.timezone("Europe/London")
    now_uk = datetime.now(uk_tz)
    
    try:
        # Clean up the date string
        date_str = date_str.strip()
        
        # Extract time part (everything after •)
        if "•" in date_str:
            parts = date_str.split("•")
            date_part = parts[0].strip()
            time_part = parts[1].strip() if len(parts) > 1 else ""
        else:
            date_part = date_str
            time_part = ""
        
        # Handle relative dates
        date_part_lower = date_part.lower()
        if date_part_lower == "today":
            target_date = now_uk.date()
        elif date_part_lower == "tomorrow":
            target_date = (now_uk + timedelta(days=1)).date()
        elif date_part_lower == "yesterday":
            target_date = (now_uk - timedelta(days=1)).date()
        elif date_part_lower in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            # Find next occurrence of this day
            day_map = {
                "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                "friday": 4, "saturday": 5, "sunday": 6
            }
            target_weekday = day_map[date_part_lower]
            current_weekday = now_uk.weekday()
            days_ahead = (target_weekday - current_weekday) % 7
            if days_ahead == 0:
                days_ahead = 7  # If today is the same day, get next week
            target_date = (now_uk + timedelta(days=days_ahead)).date()
        else:
            # Try to parse as absolute date
            # Remove day name if present (e.g., "Sat, Nov 22" -> "Nov 22")
            date_part_clean = re.sub(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s*', '', date_part, flags=re.I)
            try:
                parsed_date = date_parser.parse(date_part_clean, default=now_uk)
                target_date = parsed_date.date()
            except:
                # If parsing fails, try with current year
                try:
                    parsed_date = date_parser.parse(f"{date_part_clean} {now_uk.year}", default=now_uk)
                    target_date = parsed_date.date()
                except:
                    if debug:
                        print(f"Could not parse date part: '{date_part}'", file=sys.stderr)
                    return None
        
        # Parse time if available
        if time_part:
            # Remove timezone abbreviations (CST, PST, EST, etc.)
            time_part = re.sub(r'\s*(CST|PST|EST|GMT|BST|UTC)', '', time_part, flags=re.I)
            time_part = time_part.strip()
            
            try:
                # Parse time (handles formats like "9:00 PM", "11:00 AM")
                parsed_time = date_parser.parse(time_part, default=now_uk)
                target_time = parsed_time.time()
            except:
                if debug:
                    print(f"Could not parse time part: '{time_part}'", file=sys.stderr)
                return None
        else:
            target_time = datetime.min.time()
        
        # Combine date and time, set timezone
        dt = datetime.combine(target_date, target_time)
        dt = uk_tz.localize(dt)
        
        return dt
        
    except Exception as e:
        if debug:
            print(f"Error parsing datetime '{date_str}': {e}", file=sys.stderr)
        return None


def fetch_events(location: str, pages: int, per_page: int, sleep: float, google_api_key: str = None, debug: bool = False):
    """
    Scrape Eventbrite website to fetch events by location.
    
    Args:
        location: Search location (e.g., "Edinburgh, United Kingdom")
        pages: Number of pages to scrape
        per_page: Maximum results per page
        sleep: Delay between requests in seconds
        google_api_key: Google Maps API key for geocoding
        debug: Enable debug output
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    items = []
    seen_event_ids = set()  # Track seen event IDs to avoid duplicates
    for page_num in range(1, pages + 1):
        search_url = build_search_url(location, page_num)
        
        if debug:
            print(f"\n=== DEBUG: Page {page_num} ===", file=sys.stderr)
            print(f"URL: {search_url}", file=sys.stderr)
        
        try:
            r = requests.get(search_url, headers=headers, timeout=30)
            r.raise_for_status()
            
            if debug:
                print(f"Status Code: {r.status_code}", file=sys.stderr)
                print(f"Response Size: {len(r.text)} bytes", file=sys.stderr)
                
        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to fetch page {page_num}: {e}", file=sys.stderr)
            if page_num == 1:
                raise RuntimeError(f"Failed to fetch events from Eventbrite: {e}")
            break

        soup = BeautifulSoup(r.text, 'lxml')
        
        if debug:
            print(f"Page Title: {soup.title.string if soup.title else 'N/A'}", file=sys.stderr)
        
        # Find event cards - Eventbrite uses div.event-card
        event_elements = soup.select('div.event-card')
        
        if debug:
            print(f"Found {len(event_elements)} event cards", file=sys.stderr)
        
        # Fallback: look for event links if no cards found
        if not event_elements:
            event_elements = soup.find_all('a', href=re.compile(r'/e/[^/]+-\d+'))
        
        if not event_elements:
            if debug:
                print(f"\n⚠ WARNING: No events found on page {page_num}", file=sys.stderr)
                print(f"URL: {search_url}", file=sys.stderr)
            elif page_num == 1:
                print(f"Warning: No events found on first page. URL: {search_url}", file=sys.stderr)
                print(f"Debug: Page title: {soup.title.string if soup.title else 'N/A'}", file=sys.stderr)
                print(f"Tip: Run with --debug to see detailed diagnostic information", file=sys.stderr)
        
        page_items = 0
        for event_elem in event_elements:
            if page_items >= per_page:
                break
            
            try:
                # Extract event ID first from data attribute (more reliable)
                event_id = None
                if event_elem.has_attr('data-event-id'):
                    event_id = event_elem.get('data-event-id')
                
                # Extract event URL
                event_url = None
                if event_elem.name == 'a':
                    event_url = event_elem.get('href', '')
                    # Also check for data-event-id on the link itself
                    if not event_id and event_elem.has_attr('data-event-id'):
                        event_id = event_elem.get('data-event-id')
                else:
                    link = event_elem.find('a', href=re.compile(r'/e/[^/]+-\d+'))
                    if link:
                        event_url = link.get('href', '')
                        if not event_id and link.has_attr('data-event-id'):
                            event_id = link.get('data-event-id')
                
                if not event_url:
                    continue
                
                if not event_url.startswith('http'):
                    # Handle both .com and .co.uk domains
                    if event_url.startswith('/'):
                        event_url = urljoin('https://www.eventbrite.com', event_url)
                    else:
                        event_url = 'https://www.eventbrite.com/' + event_url
                
                # If we don't have event_id from data attribute, extract from URL
                if not event_id:
                    event_id = extract_event_id_from_url(event_url)
                
                if not event_id:
                    if debug:
                        print(f"Warning: Could not extract event ID from: {event_url}", file=sys.stderr)
                    continue
                
                # Skip if we've already seen this event ID
                if event_id in seen_event_ids:
                    continue
                seen_event_ids.add(event_id)
                
                # Extract event name - Eventbrite uses h3 with event-card classes
                name_elem = event_elem.select_one('h3.event-card__clamp-line--two, h3[class*="event-card"]')
                if not name_elem:
                    # Fallback: get from aria-label on link
                    link = event_elem.find('a', href=re.compile(r'/e/'))
                    if link and link.has_attr('aria-label'):
                        aria_label = link.get('aria-label', '')
                        name = aria_label[5:] if aria_label.startswith('View ') else aria_label
                    else:
                        name = "Event"
                else:
                    name = name_elem.get_text(strip=True)
                
                # Description not typically available on listing page
                description = ""
                
                # Extract date/time - Eventbrite uses Typography classes
                # Date appears as: "Today • 2:00 PM" or "Tomorrow • 11:00 AM"
                date_elem = None
                # Find p tags and check which one looks like a date
                p_tags = event_elem.find_all('p')
                for p in p_tags:
                    text = p.get_text(strip=True)
                    # Look for patterns like "Today •", "Tomorrow •", or date-like patterns
                    if re.search(r'(Today|Tomorrow|Yesterday|Mon|Tue|Wed|Thu|Fri|Sat|Sun)', text, re.I) or ('•' in text and any(word in text.lower() for word in ['am', 'pm', 'today', 'tomorrow'])):
                        date_elem = p
                        break
                
                # Fallback to selectors
                if not date_elem:
                    date_elem = event_elem.select_one('[data-automation="event-date"], .event-date, time')
                date_str = date_elem.get_text(strip=True) if date_elem else ""
                start_time = date_str if date_str else None
                
                # Extract venue/location - appears after date, typically in a p tag
                venue_elem = None
                # Look for the p tag that comes after the date (typically venue)
                p_tags = event_elem.find_all('p')
                date_found = False
                for p in p_tags:
                    text = p.get_text(strip=True)
                    if date_found and text and not re.search(r'(Today|Tomorrow|Yesterday|Mon|Tue|Wed|Thu|Fri|Sat|Sun)', text, re.I) and '•' not in text:
                        # This is likely the venue
                        venue_elem = p
                        break
                    if date_elem and p == date_elem:
                        date_found = True
                
                # Fallback to selectors
                if not venue_elem:
                    venue_elem = event_elem.select_one('[data-automation="event-venue"], .event-venue, .venue')
                venue_name = venue_elem.get_text(strip=True) if venue_elem else ""
                
                # Address is usually the same as venue on listing pages
                address = venue_name if venue_name else ""
                
                # Skip if address is invalid
                if not address or address.strip() == "" or "Check ticket price on event" in address:
                    if debug:
                        print(f"Skipping event '{name}' - invalid address: '{address}'", file=sys.stderr)
                    continue
                
                # Geocode the address
                if google_api_key:
                    try:
                        coordinates = geocode_address(address, google_api_key, location_context=location, debug=debug)
                        if not coordinates:
                            if debug:
                                print(f"Skipping event '{name}' - geocoding failed for address: '{address}'", file=sys.stderr)
                            continue
                        latitude, longitude = coordinates
                    except ValueError as e:
                        # REQUEST_DENIED or other configuration error
                        error_msg = str(e)
                        if "REQUEST_DENIED" in error_msg:
                            raise RuntimeError("Google Maps API configuration error.")
                        raise
                else:
                    if debug:
                        print(f"Warning: No Google Maps API key provided, skipping geocoding", file=sys.stderr)
                    continue  # Skip events if no API key
                
                # Parse datetime
                event_datetime = parse_event_datetime(start_time, debug=debug)
                if not event_datetime:
                    if debug:
                        print(f"Warning: Could not parse datetime '{start_time}' for event '{name}'", file=sys.stderr)
                    # Don't skip, but set time to None
                
                # Build new format event object
                event_data = {
                    "location_name": address,
                    "activity_name": name,
                    "latitude": latitude,
                    "longitude": longitude,
                    "time": event_datetime,
                }
                
                # Add url if exists
                if event_url:
                    event_data["url"] = event_url
                
                # Add description if exists and non-empty
                if description and description.strip():
                    event_data["description"] = description
                
                items.append(event_data)
                
                page_items += 1
                
                # Add small delay between geocoding requests to respect rate limits
                if google_api_key:
                    time.sleep(0.1)
                
            except Exception as e:
                print(f"Warning: Error parsing event element: {e}", file=sys.stderr)
                continue
        
        if page_items == 0:
            # No more events found
            break
        
        # Respect rate limits
        if page_num < pages:
            time.sleep(sleep)
    
    return items

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def get_events(location: str, google_api_key: str = None, pages: int = 3, per_page: int = 50, sleep: float = 1.0, debug: bool = False, today_only: bool = False) -> list:
    """
    Scrape Eventbrite website to fetch events by location and return as a list.
    
    This function returns events in the same format as the JSON output file:
    - location_name: string
    - activity_name: string
    - latitude: float
    - longitude: float
    - time: ISO format datetime string (not datetime object)
    - url: string (optional)
    
    Args:
        location: Search location (e.g., "Edinburgh, United Kingdom")
        google_api_key: Google Maps API key for geocoding (or set GOOGLE_MAPS_API_KEY env var)
        pages: Number of pages to scrape (default: 3)
        per_page: Maximum results per page (default: 50)
        sleep: Delay between requests in seconds (default: 1.0)
        debug: Enable debug output (default: False)
        today_only: If True, only return events happening today (default: False)
    
    Returns:
        List of event dictionaries with ISO-formatted datetime strings
    
    Raises:
        ValueError: If Google Maps API key is not provided
        RuntimeError: If scraping fails
    """
    # Load environment variables
    load_dotenv()
    
    # Get Google Maps API key
    api_key = google_api_key or os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise ValueError("Google Maps API key is required. Set GOOGLE_MAPS_API_KEY environment variable or provide it as a parameter.")
    
    # Fetch events
    items = fetch_events(location, pages, per_page, sleep, google_api_key=api_key, debug=debug)
    
    # Convert datetime objects to ISO format strings
    for item in items:
        if item.get("time") and isinstance(item["time"], datetime):
            item["time"] = item["time"].isoformat()
    
    # Filter to today's events if requested
    if today_only:
        uk_tz = pytz.timezone("Europe/London")
        today = datetime.now(uk_tz).date()
        filtered_items = []
        for item in items:
            if item.get("time"):
                try:
                    # Parse ISO format datetime string
                    event_dt = date_parser.parse(item["time"])
                    # Convert to UK timezone if it doesn't have timezone info
                    if event_dt.tzinfo is None:
                        event_dt = uk_tz.localize(event_dt)
                    else:
                        event_dt = event_dt.astimezone(uk_tz)
                    
                    # Compare dates (not times)
                    if event_dt.date() == today:
                        filtered_items.append(item)
                except Exception as e:
                    if debug:
                        print(f"Warning: Could not parse event time '{item.get('time')}': {e}", file=sys.stderr)
                    continue
        items = filtered_items
    
    return items

def main():
    # Load environment variables
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Scrape Eventbrite website to fetch events by location (JSON output)."
    )
    parser.add_argument("--location", default="Edinburgh, United Kingdom", help="Search location")
    parser.add_argument("--pages", type=int, default=3, help="Max number of pages to fetch")
    parser.add_argument("--per_page", type=int, default=50, help="Results per page")
    parser.add_argument("--sleep", type=float, default=1.0, help="Delay between paginated requests (seconds, default: 1.0 for respectful scraping)")
    parser.add_argument("--out", default="events_edinburgh_eventbrite_scraper.json", help="Output JSON file")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode (saves HTML files and shows diagnostic info)")
    parser.add_argument("--api-key", help="Google Maps API key (or set GOOGLE_MAPS_API_KEY env var)")
    args = parser.parse_args()
    
    # Get Google Maps API key
    google_api_key = args.api_key or os.getenv("GOOGLE_MAPS_API_KEY")
    if not google_api_key:
        print("Error: Google Maps API key is required. Set GOOGLE_MAPS_API_KEY environment variable or use --api-key", file=sys.stderr)
        sys.exit(1)

    try:
        items = fetch_events(args.location, args.pages, args.per_page, args.sleep, google_api_key=google_api_key, debug=args.debug)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Save to file with custom encoder for datetime
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)

    # Print a tiny preview to stdout
    print(json.dumps(items[:5], ensure_ascii=False, cls=DateTimeEncoder))

if __name__ == "__main__":
    main()
