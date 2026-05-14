"""Configuration module for Zefirka Bot"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""

    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
    DEEPSEEK_MODEL = "deepseek-chat"

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_OWNER = os.getenv("GITHUB_OWNER")
    GITHUB_REPO = os.getenv("GITHUB_REPO")
    GITHUB_API_URL = "https://api.github.com"

    BOT_NAME = os.getenv("BOT_NAME", "Zefirka")
    USER_LANGUAGE = os.getenv("USER_LANGUAGE", "uk")
    USER_TIMEZONE = os.getenv("USER_TIMEZONE", "Europe/Kyiv")
    ALLOWED_USER_ID = int(os.getenv("TELEGRAM_USER_ID", 0))

    FOLDERS = ["Personal", "Projects", "Study", "Work", "Zefirka"]

    DATA_FILES = {
        "tasks": "Zefirka/tasks.md",
        "finances": "Zefirka/finances.md",
        "projects": "Zefirka/projects.md",
        "user_profile": "Zefirka/user_profile.md",
        "reminders": "Zefirka/reminders.md",
        "daily_plans": "Zefirka/daily_plans.md",
    }

    GITHUB_TIMEOUT = 10
    DEEPSEEK_TIMEOUT = 30
    VAULT_CACHE_TTL = 300

    WEATHER_LAT = float(os.getenv("WEATHER_LAT", "50.45"))
    WEATHER_LON = float(os.getenv("WEATHER_LON", "30.52"))

    SCHEDULER_INTERVAL = 60
    MORNING_BRIEFING_TIME = "07:00"
    EVENING_REFLECTION_TIME = "20:00"
    PROACTIVE_INACTIVITY_HOURS = 2
    PROACTIVE_CHECK_INTERVAL = 30

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = "INFO"


def get_config():
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        return ProductionConfig()
    return DevelopmentConfig()
