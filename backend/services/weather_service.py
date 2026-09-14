"""
Weather service using Open-Meteo API.
Provides current weather, forecast, and agricultural impact analysis.
"""
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from backend.config.settings import OPEN_METEO_BASE_URL


async def fetch_current_weather(latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
    """Fetch current weather conditions from Open-Meteo."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": "true",
        "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,wind_speed_10m,wind_direction_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,weathercode",
        "timezone": "auto",
        "forecast_days": 7,
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(OPEN_METEO_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            current = data.get("current_weather", {})
            hourly = data.get("hourly", {})
            daily = data.get("daily", {})
            
            return {
                "current": {
                    "temperature": current.get("temperature"),
                    "windspeed": current.get("windspeed"),
                    "winddirection": current.get("winddirection"),
                    "weathercode": current.get("weathercode"),
                    "time": current.get("time"),
                },
                "hourly": {
                    "temperature_2m": hourly.get("temperature_2m", []),
                    "relative_humidity_2m": hourly.get("relative_humidity_2m", []),
                    "precipitation_probability": hourly.get("precipitation_probability", []),
                    "precipitation": hourly.get("precipitation", []),
                    "wind_speed_10m": hourly.get("wind_speed_10m", []),
                    "wind_direction_10m": hourly.get("wind_direction_10m", []),
                    "time": hourly.get("time", []),
                },
                "daily": {
                    "temperature_2m_max": daily.get("temperature_2m_max", []),
                    "temperature_2m_min": daily.get("temperature_2m_min", []),
                    "precipitation_probability_max": daily.get("precipitation_probability_max", []),
                    "precipitation_sum": daily.get("precipitation_sum", []),
                    "weathercode": daily.get("weathercode", []),
                    "time": daily.get("time", []),
                },
                "latitude": latitude,
                "longitude": longitude,
                "fetched_at": datetime.utcnow().isoformat(),
            }
    except Exception as e:
        print(f"Weather fetch error: {e}")
        return None


def weathercode_to_condition(code: int) -> str:
    """Convert WMO weather code to human-readable condition."""
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        83: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    return weather_codes.get(code, "Unknown")


def agricultural_impact(weather: Dict[str, Any], soil_moisture: Optional[float] = None) -> Dict[str, Any]:
    """Generate agricultural impact assessment from weather data."""
    current = weather.get("current", {})
    daily = weather.get("daily", {})
    hourly = weather.get("hourly", {})
    
    impacts = []
    recommendations = []
    
    # Rain probability analysis
    if daily.get("precipitation_probability_max"):
        max_rain_prob = max(daily["precipitation_probability_max"])
        if max_rain_prob >= 70:
            impacts.append(f"High rain probability ({max_rain_prob}%) expected in next 7 days")
            recommendations.append("Consider delaying irrigation if significant rainfall is forecast")
        elif max_rain_prob >= 40:
            impacts.append(f"Moderate rain probability ({max_rain_prob}%) expected")
            recommendations.append("Monitor soil moisture before scheduling irrigation")
        else:
            impacts.append("Low rain probability in forecast")
    
    # Temperature analysis
    if daily.get("temperature_2m_max") and daily.get("temperature_2m_min"):
        max_temp = max(daily["temperature_2m_max"])
        min_temp = min(daily["temperature_2m_min"])
        avg_temp = (max_temp + min_temp) / 2
        
        if avg_temp > 35:
            impacts.append(f"High temperatures (avg {avg_temp:.1f}°C) increase evaporation")
            recommendations.append("Consider early morning/evening irrigation to reduce evaporation loss")
        elif avg_temp < 10:
            impacts.append(f"Low temperatures (avg {avg_temp:.1f}°C) may slow crop growth")
    
    # Humidity analysis
    if "relative_humidity_2m" in hourly:
        humidity_values = hourly["relative_humidity_2m"]
        if humidity_values:
            avg_humidity = sum(humidity_values[:24]) / len(humidity_values[:24])
            if avg_humidity > 85:
                impacts.append(f"High humidity ({avg_humidity:.0f}%) favors fungal disease development")
                recommendations.append("Monitor crops for fungal diseases; ensure good air circulation")
            elif avg_humidity < 30:
                impacts.append(f"Low humidity ({avg_humidity:.0f}%) increases water stress risk")
    
    # Soil moisture integration
    if soil_moisture is not None:
        if soil_moisture < 35:
            impacts.append(f"Soil moisture at {soil_moisture}% - below optimal 35-55% range")
            if max_rain_prob < 30:
                recommendations.append("Consider irrigation within 24 hours")
        elif soil_moisture > 70:
            impacts.append(f"Soil moisture at {soil_moisture}% - above field capacity")
            recommendations.append("Avoid irrigation; monitor for waterlogging")
    
    return {
        "impacts": impacts,
        "recommendations": recommendations,
        "summary": f"{len(impacts)} weather impacts identified, {len(recommendations)} recommendations generated"
    }


async def get_weather_for_field(latitude: float, longitude: float, 
                                 soil_moisture: Optional[float] = None) -> Optional[Dict]:
    """Get complete weather data with agricultural impact for a field."""
    weather = await fetch_current_weather(latitude, longitude)
    if not weather:
        return None
    
    impact = agricultural_impact(weather, soil_moisture)
    
    return {
        "current": weather["current"],
        "hourly": weather["hourly"],
        "daily": weather["daily"],
        "agricultural_impact": impact,
        "fetched_at": weather["fetched_at"],
    }