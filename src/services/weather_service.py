"""Weather Service — free weather from open-meteo.com (no API key)"""

import requests
from datetime import datetime
from typing import Optional

from src.config import get_config
from src.logger import setup_logger

logger = setup_logger(__name__)
config = get_config()

WMO_CODES = {
    0: "Ясне небо",
    1: "Переважно ясно",
    2: "Мінлива хмарність",
    3: "Хмарно",
    45: "Туман",
    48: "Іній",
    51: "Легка мряка",
    53: "Помірна мряка",
    55: "Сильна мряка",
    61: "Невеликий дощ",
    63: "Помірний дощ",
    65: "Сильний дощ",
    71: "Невеликий сніг",
    73: "Помірний сніг",
    75: "Сильний сніг",
    80: "Невеликі зливи",
    81: "Помірні зливи",
    82: "Сильні зливи",
    95: "Гроза",
    96: "Гроза з градом",
    99: "Сильна гроза з градом",
}

EMOJI_MAP = {
    0: "☀️", 1: "🌤", 2: "⛅", 3: "☁️",
    45: "🌫", 48: "🌫",
    51: "🌦", 53: "🌦", 55: "🌧",
    61: "🌧", 63: "🌧", 65: "🌧",
    71: "🌨", 73: "🌨", 75: "🌨",
    80: "🌦", 81: "🌧", 82: "🌧",
    95: "⛈", 96: "⛈", 99: "⛈",
}


class WeatherService:
    """Fetches current weather from open-meteo.com"""

    def __init__(self):
        self.lat = getattr(config, "WEATHER_LAT", 50.45)
        self.lon = getattr(config, "WEATHER_LON", 30.52)
        self.api_url = "https://api.open-meteo.com/v1/forecast"
        self.timeout = 5

    def get_weather_text(self, language: str = "uk") -> str:
        data = self._fetch()
        if not data:
            return ""

        current = data.get("current", {})
        daily = data.get("daily", {})

        temp = current.get("temperature_2m")
        wmo = current.get("weathercode", 0)

        desc = WMO_CODES.get(wmo, "Невідомо")
        emoji = EMOJI_MAP.get(wmo, "")

        t_max = (daily.get("temperature_2m_max") or [None])[0]
        t_min = (daily.get("temperature_2m_min") or [None])[0]

        parts = [f"{emoji} {desc}"]
        if temp is not None:
            parts.append(f"{temp:.0f}°C")
        if t_max is not None and t_min is not None:
            parts.append(f"макс {t_max:.0f}°C, мін {t_min:.0f}°C")

        return ", ".join(parts)

    def _fetch(self) -> Optional[dict]:
        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "current": "temperature_2m,weathercode",
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "auto",
        }
        try:
            resp = requests.get(self.api_url, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                logger.debug("Weather fetched")
                return resp.json()
            logger.warning(f"Weather API {resp.status_code}")
        except Exception as e:
            logger.warning(f"Weather fetch failed: {e}")
        return None
