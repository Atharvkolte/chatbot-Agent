import requests
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a specific city."""
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_response = requests.get(geo_url).json()

        if not geo_response.get("results"):
            return f"Could not find coordinates for {city}."

        location = geo_response["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}&current_weather=true"
        )
        weather_response = requests.get(weather_url).json()

        current_weather = weather_response.get("current_weather")
        if current_weather:
            return (
                f"The current weather in {city} is "
                f"{current_weather['temperature']}°C "
                f"with wind speed {current_weather['windspeed']} km/h."
            )
        return f"Could not fetch weather data for {city}."

    except Exception as e:
        return f"Error fetching weather: {str(e)}"