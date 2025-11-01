from scrape_eventbrite import get_events

# Get list of today's events only
events = get_events("Edinburgh, United Kingdom", today_only=True)

# Print the list
print(f"Found {len(events)} events today:")
for event in events:
    print(event)

