import os
import sys

import pytest
from dotenv import load_dotenv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

load_dotenv()

if not os.getenv("GOOGLE_MAPS_API_KEY"):
    pytest.skip(
        "Eventbrite scraper test requires GOOGLE_MAPS_API_KEY credentials",
        allow_module_level=True,
    )

from api.app.utils.scrapers.scrape_eventbrite import get_events


def test_get_events_returns_list():
    events = get_events("Edinburgh, United Kingdom", today_only=True)
    assert isinstance(events, list)
