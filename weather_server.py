from mcp.server.fastmcp import FastMCP
import requests


mcp = FastMCP(
    "Weather Service",
    instructions=(
        "This MCP server provides current weather information "
        "for a city. Use the get_weather tool to retrieve "
        "current weather conditions."
    ),
)


def _get_city_location(city: str):
    geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
    geocoding_params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json",
    }

    location_response = requests.get(
        geocoding_url,
        params=geocoding_params,
        timeout=10,
    )
    location_response.raise_for_status()

    location_data = location_response.json()
    if not location_data.get("results"):
        return None

    return location_data["results"][0]

@mcp.tool()
def get_weather(city: str) -> str:
    """
    Get current weather for a city.
    """

    try:
        location = _get_city_location(city)
        if not location:
            return f"Could not find the location: {city}"

        latitude = location["latitude"]
        longitude = location["longitude"]

        location_name = location.get("name", city)
        country = location.get("country", "")

        # Get current weather
        weather_url = "https://api.open-meteo.com/v1/forecast"

        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "precipitation,"
                "rain,"
                "weather_code,"
                "wind_speed_10m"
            ),
            "timezone": "auto",
        }

        weather_response = requests.get(
            weather_url,
            params=weather_params,
            timeout=10,
        )

        weather_response.raise_for_status()

        weather_data = weather_response.json()
        current = weather_data["current"]

        result = {
            "city": location_name,
            "country": country,
            "temperature_c": current.get("temperature_2m"),
            "feels_like_c": current.get("apparent_temperature"),
            "humidity_percent": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "rain_mm": current.get("rain"),
            "weather_code": current.get("weather_code"),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "time": current.get("time"),
        }

        return str(result)

    except requests.RequestException as e:
        return f"Weather service failed: {e}"

    except Exception as e:
        return f"Unable to get weather information: {e}"


@mcp.tool()
def get_weather_forecast(city: str, days: int = 3) -> str:
    """
    Get weather forecast for the next few days for a city.
    """

    try:
        location = _get_city_location(city)
        if not location:
            return f"Could not find the location: {city}"

        days = max(1, min(days, 7))
        latitude = location["latitude"]
        longitude = location["longitude"]
        location_name = location.get("name", city)
        country = location.get("country", "")

        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
            "forecast_days": days,
            "daily": (
                "weather_code,"
                "temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_sum,"
                "rain_sum"
            ),
            "timezone": "auto",
        }

        weather_response = requests.get(
            weather_url,
            params=weather_params,
            timeout=10,
        )
        weather_response.raise_for_status()

        weather_data = weather_response.json()
        daily = weather_data.get("daily", {})
        dates = daily.get("time", [])

        daily_rows = []
        for idx, date in enumerate(dates):
            daily_rows.append(
                {
                    "date": date,
                    "weather_code": daily.get("weather_code", [None] * len(dates))[idx],
                    "temp_max_c": daily.get("temperature_2m_max", [None] * len(dates))[idx],
                    "temp_min_c": daily.get("temperature_2m_min", [None] * len(dates))[idx],
                    "precipitation_mm": daily.get("precipitation_sum", [None] * len(dates))[idx],
                    "rain_mm": daily.get("rain_sum", [None] * len(dates))[idx],
                }
            )

        result = {
            "city": location_name,
            "country": country,
            "days_requested": days,
            "forecast": daily_rows,
        }
        return str(result)

    except requests.RequestException as e:
        return f"Weather forecast service failed: {e}"

    except Exception as e:
        return f"Unable to get weather forecast: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio")