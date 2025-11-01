from collections.abc import Mapping
from typing import Any
import requests
import os
from dotenv import load_dotenv

from app.utils.scrapers.scrape_eventbrite import get_events


class ContextAggregator:
    """Collects context data used to tailor event recommendations."""
    
    def get_todays_weather_forcast(self, city, country_code):
        load_dotenv()
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")

        # First API call - Get coordinates
        coord_response = requests.get(
            "http://api.openweathermap.org/geo/1.0/direct",
            params={
                "q": f"{city},{country_code}",
                "limit": 1,
                "appid": api_key
            }
        )

        coord_data = coord_response.json()
        if coord_data and len(coord_data) > 0:
            lat = coord_data[0]['lat']
            lon = coord_data[0]['lon']

            # Second API call - Get weather forecast
            weather_response = requests.get(
                "https://api.openweathermap.org/data/2.5/weather?",
                params={
                    "lat": lat,
                    "lon": lon,
                    "exclude": "minutely,hourly",
                    "units": "metric",
                    "appid": api_key
                }
            )
            weather_response_json = weather_response.json()
            
            return {
                "temperature": weather_response_json["main"]["temp"],
                "feels_like": weather_response_json["main"]["feels_like"],
                "humidity": weather_response_json["main"]["humidity"],
                "wind_speed": weather_response_json["wind"]["speed"],
                "percent_cloudiness": weather_response_json["clouds"]["all"],
                "rain_mm_per_h": weather_response_json.get("rain"),
                "snow_mm_per_h": weather_response_json.get("snow")
            }

        return None

    def gather_context(self, response_preferences: str | None) -> Mapping[str, Any]:
        """Aggregate request preferences with default metadata."""
        # In a real implementation this would query user profiles, calendars, etc.
        normalized_preferences = (response_preferences or "").strip().lower()
        events_list  = get_events("Edinburgh, United Kingdom", today_only=True) # return a list of events which are basically dictionaries with the following keys: location_name, activity_name, latitude, longitude, time
        return {
            "preferences": normalized_preferences,
            "default_city": "Edinburgh",
            "season": "spring",
            "events": events_list,
            "weather": self.get_todays_weather_forcast(),
        }

