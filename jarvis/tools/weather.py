"""
BRO Weather - Enhanced Edition
Uses Open-Meteo API (100% free, no API key needed).
Includes caching for offline access.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try TOML
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

try:
    import tomli_w
    TOML_WRITE = True
except ImportError:
    TOML_WRITE = False


# =============================================================================
# CONFIG
# =============================================================================

# Open-Meteo API (100% FREE, no API key needed!)
GEOCODE_API = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API = "https://api.open-meteo.com/v1/forecast"

# Cache settings
CACHE_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "bro_memory"
CACHE_FILE = CACHE_DIR / "weather_cache.toml"
CACHE_DURATION_HOURS = 1  # Cache weather for 1 hour


# =============================================================================
# GEOCODING (Location to Coordinates)
# =============================================================================

def geocode(location: str) -> Optional[Dict]:
    """Convert location name to coordinates."""
    try:
        params = urllib.parse.urlencode({"name": location, "count": 1})
        url = f"{GEOCODE_API}?{params}"
        
        req = urllib.request.Request(url, headers={"User-Agent": "BRO Weather"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        
        if "results" in data and data["results"]:
            result = data["results"][0]
            return {
                "name": result.get("name", location),
                "country": result.get("country", ""),
                "lat": result["latitude"],
                "lon": result["longitude"],
                "timezone": result.get("timezone", "auto")
            }
    except Exception as e:
        print(f"Geocode error: {e}")
    return None


# =============================================================================
# CACHE MANAGEMENT
# =============================================================================

def _load_cache() -> Dict:
    """Load weather cache."""
    try:
        if CACHE_FILE.exists() and tomllib:
            with open(CACHE_FILE, "rb") as f:
                return tomllib.load(f)
    except:
        pass
    return {}


def _save_cache(data: Dict):
    """Save weather to cache."""
    CACHE_DIR.mkdir(exist_ok=True)
    try:
        if TOML_WRITE:
            with open(CACHE_FILE, "wb") as f:
                tomli_w.dump(data, f)
        else:
            # Simple TOML format
            lines = [f'# Weather cache - Updated: {datetime.now().isoformat()}']
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"\n[{key}]")
                    for k, v in value.items():
                        if isinstance(v, str):
                            lines.append(f'{k} = "{v}"')
                        else:
                            lines.append(f'{k} = {v}')
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
    except Exception as e:
        print(f"Cache save error: {e}")


def _get_cached_weather(location: str) -> Optional[Dict]:
    """Get weather from cache if still valid."""
    cache = _load_cache()
    key = location.lower().replace(" ", "_")
    
    if key in cache:
        cached = cache[key]
        cached_time = datetime.fromisoformat(cached.get("cached_at", "2000-01-01"))
        if datetime.now() - cached_time < timedelta(hours=CACHE_DURATION_HOURS):
            cached["from_cache"] = True
            return cached
    return None


def _cache_weather(location: str, weather: Dict):
    """Cache weather data."""
    cache = _load_cache()
    key = location.lower().replace(" ", "_")
    weather["cached_at"] = datetime.now().isoformat()
    cache[key] = weather
    _save_cache(cache)


# =============================================================================
# WEATHER API
# =============================================================================

def get_weather(location: str = "Bangalore") -> Dict:
    """
    Get current weather for a location.
    Uses Open-Meteo API (completely free, no API key).
    """
    # Check cache first
    cached = _get_cached_weather(location)
    if cached:
        return cached
    
    try:
        # Get coordinates
        geo = geocode(location)
        if not geo:
            return {"error": f"Location not found: {location}"}
        
        # Build API URL
        params = urllib.parse.urlencode({
            "latitude": geo["lat"],
            "longitude": geo["lon"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m",
            "timezone": geo["timezone"]
        })
        url = f"{WEATHER_API}?{params}"
        
        req = urllib.request.Request(url, headers={"User-Agent": "BRO Weather"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        
        current = data.get("current", {})
        
        weather = {
            "location": geo["name"],
            "country": geo["country"],
            "lat": geo["lat"],
            "lon": geo["lon"],
            "temp_c": current.get("temperature_2m", 0),
            "feels_like_c": current.get("apparent_temperature", 0),
            "humidity": current.get("relative_humidity_2m", 0),
            "wind_kmph": current.get("wind_speed_10m", 0),
            "wind_dir": _wind_direction(current.get("wind_direction_10m", 0)),
            "condition": _weather_code_to_text(current.get("weather_code", 0)),
            "weather_code": current.get("weather_code", 0),
            "from_cache": False
        }
        
        # Cache for offline use
        _cache_weather(location, weather)
        
        return weather
    
    except Exception as e:
        # Try to return cached data even if expired
        cache = _load_cache()
        key = location.lower().replace(" ", "_")
        if key in cache:
            cached = cache[key]
            cached["from_cache"] = True
            cached["cache_note"] = f"Offline mode - cached {cached.get('cached_at', 'unknown')}"
            return cached
        
        return {"error": str(e)}


def get_forecast(location: str = "Bangalore", days: int = 3) -> list:
    """Get weather forecast."""
    try:
        geo = geocode(location)
        if not geo:
            return [{"error": f"Location not found: {location}"}]
        
        params = urllib.parse.urlencode({
            "latitude": geo["lat"],
            "longitude": geo["lon"],
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset",
            "timezone": geo["timezone"],
            "forecast_days": days
        })
        url = f"{WEATHER_API}?{params}"
        
        req = urllib.request.Request(url, headers={"User-Agent": "BRO Weather"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        
        forecasts = []
        for i, date in enumerate(dates):
            forecasts.append({
                "date": date,
                "max_c": daily.get("temperature_2m_max", [0])[i],
                "min_c": daily.get("temperature_2m_min", [0])[i],
                "rain_chance": daily.get("precipitation_probability_max", [0])[i],
                "condition": _weather_code_to_text(daily.get("weather_code", [0])[i]),
                "sunrise": daily.get("sunrise", [""])[i].split("T")[-1] if daily.get("sunrise") else "",
                "sunset": daily.get("sunset", [""])[i].split("T")[-1] if daily.get("sunset") else "",
            })
        
        return forecasts
    
    except Exception as e:
        return [{"error": str(e)}]


# =============================================================================
# HELPERS
# =============================================================================

def _wind_direction(degrees: float) -> str:
    """Convert wind degrees to direction."""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = int((degrees + 11.25) / 22.5) % 16
    return directions[idx]


def _weather_code_to_text(code: int) -> str:
    """Convert WMO weather code to text."""
    codes = {
        0: "Clear sky",
        1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Foggy", 48: "Depositing rime fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        66: "Light freezing rain", 67: "Heavy freezing rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
        85: "Slight snow showers", 86: "Heavy snow showers",
        95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
    }
    return codes.get(code, f"Unknown ({code})")


def _get_weather_emoji(code: int) -> str:
    """Get emoji for weather code."""
    if code == 0:
        return "☀️"
    elif code in [1, 2]:
        return "🌤️"
    elif code == 3:
        return "☁️"
    elif code in [45, 48]:
        return "🌫️"
    elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        return "🌧️"
    elif code in [66, 67]:
        return "🌨️"
    elif code in [71, 73, 75, 77, 85, 86]:
        return "❄️"
    elif code in [95, 96, 99]:
        return "⛈️"
    else:
        return "🌡️"


# =============================================================================
# FORMATTED OUTPUT
# =============================================================================

def weather(location: str = "Bangalore") -> str:
    """Get formatted weather report."""
    w = get_weather(location)
    
    if "error" in w:
        return f"❌ Weather error: {w['error']}"
    
    emoji = _get_weather_emoji(w.get("weather_code", 0))
    cache_note = " (cached)" if w.get("from_cache") else ""
    
    return f"""
{emoji} WEATHER - {w['location']}, {w['country']}{cache_note}
{'='*50}

🌡️ Temperature: {w['temp_c']:.1f}°C
   Feels like: {w['feels_like_c']:.1f}°C

{emoji} Condition: {w['condition']}

💨 Wind: {w['wind_kmph']:.0f} km/h {w['wind_dir']}
💧 Humidity: {w['humidity']}%

📍 Coordinates: {w['lat']:.2f}, {w['lon']:.2f}
"""


def forecast(location: str = "Bangalore", days: int = 3) -> str:
    """Get formatted forecast."""
    fc = get_forecast(location, days)
    
    if fc and "error" in fc[0]:
        return f"❌ Forecast error: {fc[0]['error']}"
    
    w = get_weather(location)
    loc = f"{w.get('location', location)}, {w.get('country', '')}" if "error" not in w else location
    
    output = f"""
📅 {days}-DAY FORECAST - {loc}
{'='*50}
"""
    
    for day in fc:
        emoji = _get_weather_emoji(0)  # Default
        if "rain" in day["condition"].lower():
            emoji = "🌧️"
        elif "cloud" in day["condition"].lower():
            emoji = "☁️"
        elif "clear" in day["condition"].lower():
            emoji = "☀️"
        
        output += f"""
📆 {day['date']}
   {emoji} {day['condition']}
   🌡️ {day['min_c']:.0f}°C - {day['max_c']:.0f}°C
   🌧️ Rain chance: {day['rain_chance']}%
   🌅 {day['sunrise']} | 🌇 {day['sunset']}
"""
    
    return output


def quick_weather(location: str = "Bangalore") -> str:
    """One-line weather."""
    w = get_weather(location)
    
    if "error" in w:
        return f"❌ {w['error']}"
    
    emoji = _get_weather_emoji(w.get("weather_code", 0))
    cache = " (cached)" if w.get("from_cache") else ""
    return f"{emoji} {w['location']}: {w['temp_c']:.1f}°C, {w['condition']}{cache}"


def clear_cache():
    """Clear weather cache."""
    try:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
        return "🗑️ Weather cache cleared"
    except:
        return "❌ Failed to clear cache"


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="BRO Weather (Open-Meteo API)")
    parser.add_argument("command", nargs="?", default="now",
                       choices=["now", "forecast", "quick", "cache", "clear"])
    parser.add_argument("location", nargs="?", default="Bangalore")
    parser.add_argument("-d", "--days", type=int, default=3, help="Forecast days")
    
    args = parser.parse_args()
    
    if args.command == "now":
        print(weather(args.location))
    elif args.command == "forecast":
        print(forecast(args.location, args.days))
    elif args.command == "quick":
        print(quick_weather(args.location))
    elif args.command == "cache":
        cache = _load_cache()
        print(f"Cached locations: {list(cache.keys())}")
    elif args.command == "clear":
        print(clear_cache())
