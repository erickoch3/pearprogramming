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


def fetch_events(location: str, pages: int, per_page: int, sleep: float, debug: bool = False):
    """Scrape Eventbrite website to fetch events by location."""
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
                address = venue_name
                
                # Extract price - most events show "Check ticket price on event"
                price_elem = event_elem.select_one('[data-automation="event-price"], .event-price, .price')
                price_text = price_elem.get_text(strip=True) if price_elem else ""
                is_free = "free" in price_text.lower() or price_text == "" or "£0" in price_text or "Check ticket price" in price_text
                
                # Extract image/logo
                img_elem = event_elem.select_one('img.event-card-image')
                logo_url = None
                if img_elem:
                    logo_url = img_elem.get('src', '') or img_elem.get('data-src', '')
                    if logo_url and not logo_url.startswith('http'):
                        logo_url = urljoin('https://www.eventbrite.com', logo_url)
                
                items.append({
                    "id": event_id,
                    "name": name,
                    "description": description,
                    "start": start_time,
                    "end": None,
                    "timezone": None,
                    "url": event_url,
                    "status": "live",
                    "is_free": is_free,
                    "currency": "GBP" if "£" in price_text else "USD",
                    "logo": logo_url,
                    "venue": {
                        "id": None,
                        "name": venue_name,
                        "latitude": None,
                        "longitude": None,
                        "address": address,
                    },
                    "category_id": None,
                    "subcategory_id": None,
                    "capacity": None,
                    "shareable": True,
                    "source": "eventbrite_web_scraper"
                })
                
                page_items += 1
                
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

def main():
    parser = argparse.ArgumentParser(
        description="Scrape Eventbrite website to fetch events by location (JSON output)."
    )
    parser.add_argument("--location", default="Edinburgh, United Kingdom", help="Search location")
    parser.add_argument("--pages", type=int, default=3, help="Max number of pages to fetch")
    parser.add_argument("--per_page", type=int, default=50, help="Results per page")
    parser.add_argument("--sleep", type=float, default=1.0, help="Delay between paginated requests (seconds, default: 1.0 for respectful scraping)")
    parser.add_argument("--out", default="events_edinburgh_eventbrite_scraper.json", help="Output JSON file")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode (saves HTML files and shows diagnostic info)")
    args = parser.parse_args()

    try:
        items = fetch_events(args.location, args.pages, args.per_page, args.sleep, debug=args.debug)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    # Print a tiny preview to stdout
    print(json.dumps(items[:5], ensure_ascii=False))

if __name__ == "__main__":
    main()
