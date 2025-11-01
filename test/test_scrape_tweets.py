import os
import sys
from datetime import datetime

import pytest

pytestmark = pytest.mark.integration

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.models.tweet import Tweet

dotenv = pytest.importorskip("dotenv")
dotenv.load_dotenv()


@pytest.fixture(scope="module")
def twitter_api_credentials() -> None:
    if not os.getenv("X_API_KEY"):
        pytest.skip(
            "LIVE tweet scraper test requires X_API_KEY credentials",
            allow_module_level=True,
        )


def test_get_tweets(twitter_api_credentials):
    """Smoke-test get_tweets when X credentials are configured."""
    from app.utils.scrapers.scrape_tweets import get_tweets

    tweets = get_tweets(limit=3, threshold_hours_for_refresh=2)

    assert isinstance(tweets, list)
    assert tweets, "Expected at least one tweet"

    for tweet in tweets:
        assert isinstance(tweet, Tweet)
        assert isinstance(tweet.text, str) and tweet.text
        assert isinstance(tweet.like_count, int) and tweet.like_count >= 0
        assert isinstance(tweet.retweet_count, int) and tweet.retweet_count >= 0
        if tweet.created_at is not None:
            assert isinstance(tweet.created_at, datetime)
        assert isinstance(tweet.scraped_at, datetime)
