"""Daily Routine — morning briefing (with weather) and evening reflection"""

import json
import os
from datetime import datetime
from typing import Optional

from src.services.github_service import GitHubService
from src.services.deepseek_service import DeepseekService
from src.services.weather_service import WeatherService
from src.logger import setup_logger

logger = setup_logger(__name__)
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
STATE_FILE = os.path.join(DATA_DIR, "scheduler_state.json")

MORNING_PROMPT = """You are Zefirka, a personal AI assistant. Generate a short morning briefing.

Today is {date}.
User language: {language}.
Weather: {weather}

Here is the user's current state:
{tasks}
{finances}
{reminders}
{plans}

Write a friendly morning message (4-6 sentences) in {language}:
- Greet the user by name ({name})
- Mention today's weather naturally
- Mention today's top urgent/important task
- Give a budget note if spending is significant
- Mention any reminders for today
- End with encouragement

Write ONLY the message text. No markdown, no quotes, no labels."""

EVENING_PROMPT = """You are Zefirka, a personal AI assistant. Prompt the user for evening reflection.

Today is {date}.
User language: {language}.

User's name: {name}

Write a short message (2-3 sentences) in {language}:
- Ask how the day went
- Ask what was accomplished
- Ask about mood
- Offer to help plan tomorrow

Write ONLY the message text. No markdown. No quotes."""


class DailyRoutineService:
    def __init__(self):
        self.github = GitHubService()
        self.deepseek = DeepseekService()
        self.weather = WeatherService()

    def get_morning_briefing(self, language: str = "uk") -> Optional[str]:
        today = datetime.now().strftime("%Y-%m-%d")
        state = self._load_state()
        if state.get("morning_briefing_date") == today:
            return None

        tasks = self.github.read_file_content("Zefirka/tasks.md") or ""
        finances = self.github.read_file_content("Zefirka/finances.md") or ""
        reminders = self.github.read_file_content("Zefirka/reminders.md") or ""
        plans = self.github.read_file_content("Zefirka/daily_plans.md") or ""
        profile = self.github.read_file_content("Zefirka/user_profile.md") or ""
        weather = self.weather.get_weather_text(language) or ""

        name = "User"
        for line in profile.split("\n"):
            if "- **Name:**" in line:
                name = line.split("**Name:**")[-1].strip()

        prompt = MORNING_PROMPT.format(
            date=today, language=language, name=name,
            weather=weather,
            tasks=tasks[:500], finances=finances[:500],
            reminders=reminders[:300], plans=plans[:300],
        )

        msg = self._ask_ai(prompt)
        if msg:
            state["morning_briefing_date"] = today
            self._save_state(state)
            logger.info("Morning briefing with weather generated")
        return msg

    def get_evening_reflection(self, language: str = "uk") -> Optional[str]:
        today = datetime.now().strftime("%Y-%m-%d")
        state = self._load_state()
        if state.get("evening_reflection_date") == today:
            return None

        profile = self.github.read_file_content("Zefirka/user_profile.md") or ""
        name = "User"
        for line in profile.split("\n"):
            if "- **Name:**" in line:
                name = line.split("**Name:**")[-1].strip()

        prompt = EVENING_PROMPT.format(date=today, language=language, name=name)
        msg = self._ask_ai(prompt)
        if msg:
            state["evening_reflection_date"] = today
            self._save_state(state)
            logger.info("Evening reflection generated")
        return msg

    def _ask_ai(self, prompt: str) -> Optional[str]:
        decision = self.deepseek.analyze_request(prompt, "", "", "uk")
        return decision.get("response") or None

    def _load_state(self) -> dict:
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_state(self, data: dict):
        try:
            with open(STATE_FILE) as f:
                existing = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing = {}
        existing.update(data)
        with open(STATE_FILE, "w") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
