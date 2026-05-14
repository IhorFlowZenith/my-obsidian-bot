"""Scheduler — background loop for reminders, routines, analytics, proactive"""

import asyncio
import json
import os
from datetime import datetime
from typing import Optional

from src.services.reminder_service import ReminderService
from src.services.daily_routine import DailyRoutineService
from src.services.proactive_service import ProactiveService
from src.services.analytics_service import AnalyticsService
from src.config import get_config
from src.logger import setup_logger

logger = setup_logger(__name__)
config = get_config()
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
CHAT_ID_FILE = os.path.join(DATA_DIR, "chat_id.json")


class BotScheduler:
    """Orchestrates background tasks every 60s"""

    def __init__(self, bot):
        self.bot = bot
        self.reminder_svc = ReminderService()
        self.routine_svc = DailyRoutineService()
        self.proactive_svc = ProactiveService()
        self.analytics_svc = AnalyticsService()
        self._last_active: Optional[datetime] = None

    def update_last_active(self):
        self._last_active = datetime.now()

    async def run(self):
        logger.info("Scheduler started")
        while True:
            try:
                await self._tick()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            await asyncio.sleep(config.SCHEDULER_INTERVAL)

    async def _tick(self):
        now = datetime.now()
        lang = config.USER_LANGUAGE
        current = now.strftime("%H:%M")

        # 1. Reminders (every tick)
        for msg in self.reminder_svc.check():
            await self._send(msg)

        # 2. Morning briefing 07:00
        if current == config.MORNING_BRIEFING_TIME:
            msg = self.routine_svc.get_morning_briefing(lang)
            if msg:
                await self._send(msg)

        # 3. Evening reflection 20:00
        if current == config.EVENING_REFLECTION_TIME:
            msg = self.routine_svc.get_evening_reflection(lang)
            if msg:
                await self._send(msg)
            daily = self.analytics_svc.get_daily_summary(lang)
            if daily:
                await self._send(daily)

        # 4. Weekly digest (Monday 09:00)
        if current == "09:00" and now.weekday() == 0:
            msg = self.analytics_svc.get_weekly_digest(lang)
            if msg:
                await self._send(msg)

        # 5. Budget alerts (every 30 min)
        if int(now.strftime("%M")) % 30 == 0:
            for alert in self.analytics_svc.check_budget_alerts(lang):
                await self._send(alert)

        # 6. Proactive check
        if int(now.strftime("%M")) % config.PROACTIVE_CHECK_INTERVAL == 0:
            msg = self.proactive_svc.check(self._last_active)
            if msg:
                await self._send(msg)

    async def _send(self, text: str):
        chat_id = self._get_chat_id()
        if not chat_id:
            return
        try:
            await self.bot.send_message(chat_id=chat_id, text=text[:4096])
            logger.debug(f"Sent: {text[:60]}")
        except Exception as e:
            logger.error(f"Send failed: {e}")

    def _get_chat_id(self) -> Optional[int]:
        try:
            with open(CHAT_ID_FILE) as f:
                data = json.load(f)
            return data.get("chat_id")
        except (FileNotFoundError, json.JSONDecodeError):
            return None
