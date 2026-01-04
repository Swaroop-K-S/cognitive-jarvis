"""
BRO Weather
Get current weather and forecast (uses free API).
"""

import os
import sys
import json
import urllib.request
from typing import Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# WEATHER API (Free - wttr.in)
# =============================================================================

WEATHER_API = "https://wttr.in"


def get_weather(location: str = None) -> Dict:
    """
    Get current weather for a location.
    If no location, uses IP-based location.
    """
    try:
        loc = location.replace(" ", "+") if location else ""
        url = f"{WEATHER_API}/{loc}?format=j1"
        
        req = urllib.request.Request(url, headers={"User-Agent": "BRO Weather"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        
        current = data["current_condition"][0]
        area = data["nearest_area"][0]
        
        return {
            "location": area["areaName"][0]["value"],
            "region": area["region"][0]["value"],
            "country": area["country"][0]["value"],
            "temp_c": int(current["temp_C"]),
            "temp_f": int(current["temp_F"]),
            "feels_like_c": int(current["FeelsLikeC"]),
            "condition": current["weatherDesc"][0]["value"],
            "humidity": int(current["humidity"]),
            "wind_kmph": int(current["windspeedKmph"]),
            "wind_dir": current["winddir16Point"],
            "uv": int(current["uvIndex"]),
            "visibility": int(current["visibility"]),
        }
    except Exception as e:
        return {"error": str(e)}


def get_forecast(location: str = None, days: int = 3) -> list:
    """Get weather forecast."""
    try:
        loc = location.replace(" ", "+") if location else ""
        url = f"{WEATHER_API}/{loc}?format=j1"
        
        req = urllib.request.Request(url, headers={"User-Agent": "BRO Weather"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        
        forecasts = []
        for day in data["weather"][:days]:
            forecasts.append({
                "date": day["date"],
                "max_c": int(day["maxtempC"]),
                "min_c": int(day["mintempC"]),
                "condition": day["hourly"][4]["weatherDesc"][0]["value"],  # Midday
                "rain_chance": max(int(h.get("chanceofrain", 0)) for h in day["hourly"]),
                "sunrise": day["astronomy"][0]["sunrise"],
                "sunset": day["astronomy"][0]["sunset"],
            })
        
        return forecasts
    except Exception as e:
        return [{"error": str(e)}]


# =============================================================================
# FORMATTED OUTPUT
# =============================================================================

def weather(location: str = None) -> str:
    """Get formatted weather report."""
    w = get_weather(location)
    
    if "error" in w:
        return f"❌ Weather error: {w['error']}"
    
    # Weather emoji
    condition = w["condition"].lower()
    if "sun" in condition or "clear" in condition:
        emoji = "☀️"
    elif "cloud" in condition:
        emoji = "☁️"
    elif "rain" in condition:
        emoji = "🌧️"
    elif "storm" in condition or "thunder" in condition:
        emoji = "⛈️"
    elif "snow" in condition:
        emoji = "❄️"
    elif "fog" in condition or "mist" in condition:
        emoji = "🌫️"
    else:
        emoji = "🌤️"
    
    return f"""
{emoji} WEATHER - {w['location']}, {w['region']}
{'='*45}

🌡️ Temperature: {w['temp_c']}°C ({w['temp_f']}°F)
   Feels like: {w['feels_like_c']}°C

{emoji} Condition: {w['condition']}

💨 Wind: {w['wind_kmph']} km/h {w['wind_dir']}
💧 Humidity: {w['humidity']}%
👁️ Visibility: {w['visibility']} km
☀️ UV Index: {w['uv']}
"""


def forecast(location: str = None, days: int = 3) -> str:
    """Get formatted forecast."""
    fc = get_forecast(location, days)
    
    if fc and "error" in fc[0]:
        return f"❌ Forecast error: {fc[0]['error']}"
    
    w = get_weather(location)
    loc = f"{w.get('location', 'Unknown')}, {w.get('region', '')}" if "error" not in w else "Unknown"
    
    output = f"""
📅 {days}-DAY FORECAST - {loc}
{'='*45}
"""
    
    for day in fc:
        # Emoji
        condition = day["condition"].lower()
        if "sun" in condition or "clear" in condition:
            emoji = "☀️"
        elif "rain" in condition:
            emoji = "🌧️"
        elif "cloud" in condition:
            emoji = "☁️"
        else:
            emoji = "🌤️"
        
        output += f"""
📆 {day['date']}
   {emoji} {day['condition']}
   🌡️ {day['min_c']}°C - {day['max_c']}°C
   🌧️ Rain chance: {day['rain_chance']}%
   🌅 {day['sunrise']} | 🌇 {day['sunset']}
"""
    
    return output


def quick_weather(location: str = None) -> str:
    """One-line weather."""
    w = get_weather(location)
    
    if "error" in w:
        return f"❌ {w['error']}"
    
    return f"🌡️ {w['location']}: {w['temp_c']}°C, {w['condition']}"


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="BRO Weather")
    parser.add_argument("command", nargs="?", default="now",
                       choices=["now", "forecast", "quick"])
    parser.add_argument("location", nargs="?", default=None)
    
    args = parser.parse_args()
    
    if args.command == "now":
        print(weather(args.location))
    elif args.command == "forecast":
        print(forecast(args.location))
    elif args.command == "quick":
        print(quick_weather(args.location))
