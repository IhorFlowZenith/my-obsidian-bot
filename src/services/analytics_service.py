"""Analytics Service — weekly digest, budget alerts, daily summary"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Optional, List

from src.services.github_service import GitHubService
from src.services.deepseek_service import DeepseekService
from src.config import get_config
from src.logger import setup_logger

logger = setup_logger(__name__)
config = get_config()
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
STATE_FILE = os.path.join(DATA_DIR, "scheduler_state.json")

WEEKLY_PROMPT = """You are Zefirka, a personal AI assistant. Generate a weekly digest.

Today is {date}, {weekday_name}. 
User language: {language}.

Current state:
--- TASKS ---
{tasks}
--- FINANCES ---
{finances}  
--- PROJECTS ---
{projects}

Write a friendly weekly digest (4-6 sentences) in {language}:
1. Greeting
2. Task summary: how many pending, what's urgent
3. Expense summary: total spent, biggest category
4. Project progress
5. Tip or encouragement

Write ONLY the message. No markdown. No labels."""

BUDGET_PROMPT = """You are Zefirka. Alert the user about budget.

{finances}

Category "{category}" has spent {spent}/{limit} UAH ({percent}%).
User language: {language}.

Write 1-2 sentences in {language} warning about this. Be friendly.
Write ONLY the message. No markdown."""

DAILY_SUMMARY_PROMPT = """You are Zefirka. Write a daily summary for today.

Today: {date}
Language: {language}

Today's data:
--- TASKS ---
{tasks}
--- EXPENSES ---
{finances}

Write a short daily summary (3-4 sentences) in markdown format:
## Daily Summary - {date}
- Tasks completed: X/Y
- Expenses: X UAH total
- Notes: ...

Write ONLY the summary content, ready to append to daily_plans.md."""


class AnalyticsService:
    """Generates weekly digests, budget alerts, and daily summaries"""

    def __init__(self):
        self.github = GitHubService()
        self.deepseek = DeepseekService()

    def get_weekly_digest(self, language: str = "uk") -> Optional[str]:
        state = self._load_state()
        last_week = state.get("last_weekly_digest_week")
        today = datetime.now()
        week_num = today.isocalendar()[1]

        if last_week == week_num:
            return None

        # Only run on Monday
        if today.weekday() != 0:
            return None

        tasks = self.github.read_file_content("Zefirka/tasks.md") or ""
        finances = self.github.read_file_content("Zefirka/finances.md") or ""
        projects = self.github.read_file_content("Zefirka/projects.md") or ""

        weekday_names = {
            "uk": "понеділок,вівторок,середа,четвер,п'ятниця,субота,неділя",
        }
        wd = weekday_names.get(language, "").split(",")
        wd_name = wd[today.weekday()] if len(wd) > today.weekday() else ""

        prompt = WEEKLY_PROMPT.format(
            date=today.strftime("%Y-%m-%d"),
            weekday_name=wd_name,
            language=language,
            tasks=tasks[:800],
            finances=finances[:800],
            projects=projects[:500],
        )

        msg = self._ask(prompt)
        if msg:
            state["last_weekly_digest_week"] = week_num
            self._save_state(state)
            logger.info(f"Weekly digest generated (week {week_num})")
        return msg

    def check_budget_alerts(self, language: str = "uk") -> List[str]:
        state = self._load_state()
        today_str = datetime.now().strftime("%Y-%m-%d")
        alerted = set(state.get("budget_alerts_sent", []))
        alerts = []

        finances = self.github.read_file_content("Zefirka/finances.md")
        if not finances:
            return []

        # Parse budget sections like: "### Food\n- Limit: 3000\n- Spent: 2700"
        sections = re.split(r"###\s+", finances)
        for section in sections:
            if not section.strip():
                continue
            lines = section.strip().split("\n")
            if len(lines) < 3:
                continue
            cat_name = lines[0].strip()
            limit_match = re.search(r"Limit:\s*([\d\s,]+)", section)
            spent_match = re.search(r"Spent:\s*([\d\s,]+)", section)
            if not limit_match or not spent_match:
                continue
            try:
                limit = float(limit_match.group(1).replace(" ", "").replace(",", ""))
                spent = float(spent_match.group(1).replace(" ", "").replace(",", ""))
            except ValueError:
                continue
            if limit == 0:
                continue
            pct = (spent / limit) * 100
            key = f"{cat_name}|{today_str}"

            if pct >= 80 and key not in alerted:
                prompt = BUDGET_PROMPT.format(
                    finances=finances[:500],
                    category=cat_name,
                    spent=int(spent),
                    limit=int(limit),
                    percent=int(pct),
                    language=language,
                )
                msg = self._ask(prompt)
                if msg:
                    alerts.append(msg)
                    alerted.add(key)
                    logger.info(f"Budget alert: {cat_name} at {int(pct)}%")

        state["budget_alerts_sent"] = sorted(alerted)
        self._save_state(state)
        return alerts

    def get_daily_summary(self, language: str = "uk") -> Optional[str]:
        state = self._load_state()
        today_str = datetime.now().strftime("%Y-%m-%d")
        if state.get("last_daily_summary") == today_str:
            return None

        tasks = self.github.read_file_content("Zefirka/tasks.md") or ""
        finances = self.github.read_file_content("Zefirka/finances.md") or ""

        prompt = DAILY_SUMMARY_PROMPT.format(
            date=today_str,
            language=language,
            tasks=tasks[:800],
            finances=finances[:800],
        )

        msg = self._ask(prompt)
        if msg:
            state["last_daily_summary"] = today_str
            self._save_state(state)
            self._append_summary_to_vault(msg)
            logger.info(f"Daily summary saved for {today_str}")
        return msg

    def _append_summary_to_vault(self, summary: str):
        file_path = "Zefirka/daily_plans.md"
        content = self.github.read_file_content(file_path)
        today = datetime.now().strftime("%Y-%m-%d")
        block = f"\n\n---\n{summary}\n"
        if content:
            content = content.rstrip() + block
        else:
            content = f"# Daily Plans\n\n{block}"

        sha = (self.github.get_file(file_path) or {}).get("sha")
        self.github.create_or_update_file(file_path, content, f"Daily summary {today}", sha=sha)

    def _ask(self, prompt: str) -> Optional[str]:
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
