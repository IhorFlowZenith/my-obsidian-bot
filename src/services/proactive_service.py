"""Proactive Service — smart check-ins and inactivity nudges"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional, List

from src.services.github_service import GitHubService
from src.services.deepseek_service import DeepseekService
from src.logger import setup_logger

logger = setup_logger(__name__)
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
STATE_FILE = os.path.join(DATA_DIR, "scheduler_state.json")

PROACTIVE_PROMPT = """You are Zefirka, a personal AI assistant.

The user hasn't been active for a while. Here is their current state:
{tasks}
{finances}
{reminders}

Generate a short friendly check-in message in {language} (2-3 sentences):
- Ask if everything is okay
- Mention something notable (pending task, budget, reminder)
- Offer help

Write ONLY the message. No markdown."""


class ProactiveService:
    """Sends gentle nudges when user is inactive"""

    def __init__(self):
        self.github = GitHubService()
        self.deepseek = DeepseekService()

    def check(self, last_active: Optional[datetime]) -> Optional[str]:
        state = self._load_state()
        last_check_str = state.get("last_proactive_check")
        now = datetime.now()

        if last_check_str:
            last_check = datetime.fromisoformat(last_check_str)
            if (now - last_check).total_seconds() < 1800:
                return None
        else:
            return None

        state["last_proactive_check"] = now.isoformat()
        self._save_state(state)

        if last_active and (now - last_active).total_seconds() < 7200:
            return None

        tasks = self.github.read_file_content("Zefirka/tasks.md") or ""
        finances = self.github.read_file_content("Zefirka/finances.md") or ""
        reminders = self.github.read_file_content("Zefirka/reminders.md") or ""

        prompt = PROACTIVE_PROMPT.format(
            tasks=tasks[:400],
            finances=finances[:400],
            reminders=reminders[:300],
            language="uk",
        )

        decision = self.deepseek.analyze_request(prompt, "", "", "uk")
        msg = decision.get("response")
        if msg:
            logger.info("Proactive check-in generated")
        return msg

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
