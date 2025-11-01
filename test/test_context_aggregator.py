import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../api/app/services"))
)

from context_aggregator import ContextAggregator


def test_get_todays_weather_forecast():
    """Test get_todays_weather_forcast method with real API call."""

    # Create instance
    aggregator = ContextAggregator()

    # Call the method
    response = aggregator.get_todays_weather_forcast("Edinburgh", "GB")

    # Verify response is not None
    assert response is not None, "Response should not be None"

    # Verify all expected keys are present
    expected_keys = [
        "temperature",
        "feels_like",
        "humidity",
        "wind_speed",
        "percent_cloudiness",
        "rain_mm_per_h",
        "snow_mm_per_h",
    ]

    for key in expected_keys:
        assert key in response, f"Response should contain '{key}'"

    # Verify temperature is a reasonable value
    assert isinstance(response["temperature"], (int, float)), "Temperature should be numeric"
    assert -50 < response["temperature"] < 50, "Temperature should be in reasonable range"

    # Verify humidity is a percentage
    assert isinstance(response["humidity"], int), "Humidity should be an integer"
    assert 0 <= response["humidity"] <= 100, "Humidity should be between 0 and 100"

    # Verify wind speed is non-negative
    assert isinstance(response["wind_speed"], (int, float)), "Wind speed should be numeric"
    assert response["wind_speed"] >= 0, "Wind speed should be non-negative"

    # Verify cloudiness is a percentage
    assert isinstance(response["percent_cloudiness"], int), "Cloudiness should be an integer"
    assert 0 <= response["percent_cloudiness"] <= 100, "Cloudiness should be between 0 and 100"

    print("✓ Response received successfully")
    print(f"✓ Temperature: {response['temperature']}°C")
    print(f"✓ Feels like: {response['feels_like']}°C")
    print(f"✓ Humidity: {response['humidity']}%")
    print(f"✓ Wind speed: {response['wind_speed']} m/s")
    print(f"✓ Cloudiness: {response['percent_cloudiness']}%")
    print(f"✓ Rain: {response['rain_mm_per_h']} mm/h")
    print(f"✓ Snow: {response['snow_mm_per_h']} mm/h")


if __name__ == "__main__":
    print("Running test_get_todays_weather_forecast...")
    print("=" * 50)
    try:
        test_get_todays_weather_forecast()
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
    except Exception as e:
        print(f"\n✗ Error occurred: {e}")


