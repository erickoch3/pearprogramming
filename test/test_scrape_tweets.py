import sys
import os
from datetime import datetime

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../api"))
)

from app.services.scrape_tweets import get_tweets
from app.models.tweet import Tweet


def test_get_tweets():
    """Test get_tweets function to verify it returns valid tweet data."""

    print("Fetching events from database (will refresh if needed)...")

    # Call get_tweets with a small limit for testing
    tweets = get_tweets(limit=5, threshold_hours_for_refresh=2)

    # Verify response is a list
    assert isinstance(tweets, list), "Response should be a list"

    # Verify we got some tweets
    assert len(tweets) > 0, "Should return at least one tweet"

    print(f"\n✓ Retrieved {len(tweets)} tweet(s)")

    # Verify each tweet has the expected structure
    for i, tweet in enumerate(tweets, 1):
        # Check it's a Tweet object
        assert isinstance(tweet, Tweet), f"Item {i} should be a Tweet object"

        # Check required fields exist
        assert hasattr(tweet, "id"), f"Tweet {i} should have 'id' attribute"
        assert hasattr(tweet, "text"), f"Tweet {i} should have 'text' attribute"
        assert hasattr(tweet, "like_count"), f"Tweet {i} should have 'like_count' attribute"
        assert hasattr(tweet, "retweet_count"), f"Tweet {i} should have 'retweet_count' attribute"
        assert hasattr(tweet, "created_at"), f"Tweet {i} should have 'created_at' attribute"
        assert hasattr(tweet, "scraped_at"), f"Tweet {i} should have 'scraped_at' attribute"

        # Check data types
        assert isinstance(tweet.id, int), f"Tweet {i} id should be an integer"
        assert isinstance(tweet.text, str), f"Tweet {i} text should be a string"
        assert isinstance(tweet.like_count, int), f"Tweet {i} like_count should be an integer"
        assert isinstance(tweet.retweet_count, int), f"Tweet {i} retweet_count should be an integer"

        # Check text is not empty
        assert len(tweet.text) > 0, f"Tweet {i} text should not be empty"

        # Check counts are non-negative
        assert tweet.like_count >= 0, f"Tweet {i} like_count should be non-negative"
        assert tweet.retweet_count >= 0, f"Tweet {i} retweet_count should be non-negative"

        # Check created_at is a datetime (or None)
        if tweet.created_at is not None:
            assert isinstance(tweet.created_at, datetime), f"Tweet {i} created_at should be a datetime"

        # Check scraped_at is a datetime
        assert isinstance(tweet.scraped_at, datetime), f"Tweet {i} scraped_at should be a datetime"

        # Print tweet details
        print(f"\n--- Tweet {i} ---")
        print(f"ID: {tweet.id}")
        print(f"Text: {tweet.text[:80]}{'...' if len(tweet.text) > 80 else ''}")
        print(f"Likes: {tweet.like_count}")
        print(f"Retweets: {tweet.retweet_count}")
        print(f"Created: {tweet.created_at}")
        print(f"Scraped: {tweet.scraped_at}")

    print("\n✓ All tweet objects have valid structure")
    print("✓ All data types are correct")
    print("✓ All values are within expected ranges")


if __name__ == "__main__":
    print("Running scrape_tweets tests...")
    print("=" * 70)

    try:
        test_get_tweets()
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
