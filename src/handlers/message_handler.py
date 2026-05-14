"""Message Handler — processes user messages, saves chat_id"""

import json
import os
import re
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.services import DeepseekService
from src.services.context_manager import ContextManager
from src.services.smart_action_engine import SmartActionEngine
from src.services.smart_router import SmartRouter
from src.services.scheduler import BotScheduler
from src.services.action_logger import ActionLogger
from src.config import get_config
from src.logger import setup_logger

logger = setup_logger(__name__)
config = get_config()
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
CHAT_ID_FILE = os.path.join(DATA_DIR, "chat_id.json")

FILE_CONTENT_MARKER = "__FILE_CONTENT__:"
URL_CONTENT_MARKER = "__URL_CONTENT__:"


def _save_chat_id(chat_id: int):
    with open(CHAT_ID_FILE, "w") as f:
        json.dump({"chat_id": chat_id}, f)


def _md_to_html(text: str) -> str:
    """Convert markdown to Telegram HTML"""
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"~~(.+?)~~", r"<s>\1</s>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"^###\s+(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)
    text = re.sub(r"^##\s+(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)
    return text.strip()


def _buttons_for(action: str, data: dict) -> Optional[InlineKeyboardMarkup]:
    """Create inline keyboard buttons based on action"""
    title = data.get("title", "")
    if not title:
        return None
    if action == "add_task":
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Виконано", callback_data=f"done:{title}"),
            InlineKeyboardButton("🗑 Видалити", callback_data=f"delete:{title}"),
        ]])
    return None


class MessageHandler:
    def __init__(self, language: str = "uk"):
        self.language = language
        self.deepseek = DeepseekService()
        self.context = ContextManager()
        self.engine = SmartActionEngine()
        self.router = SmartRouter()
        self.action_log = ActionLogger()
        self._scheduler: Optional[BotScheduler] = None

    def set_scheduler(self, scheduler: BotScheduler):
        self._scheduler = scheduler

    async def handle(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        msg = update.message.text
        uid = update.effective_user.id
        chat_id = update.effective_chat.id
        if config.ALLOWED_USER_ID and uid != config.ALLOWED_USER_ID:
            await update.message.reply_text("❌ Not authorized.")
            return

        _save_chat_id(chat_id)
        if self._scheduler:
            self._scheduler.update_last_active()

        self.context.add_to_history("user", msg)
        await update.message.chat.send_action("typing")

        try:
            decision = self.deepseek.analyze_request(
                msg,
                self.router.get_routing_guide(),
                self.context.get_conversation_context(),
                self.language,
            )

            if decision.get("action") == "error":
                reply = decision.get("response", "❌ Error")
                await update.message.reply_text(reply)
                self.context.add_to_history("bot", reply)
                return

            action = decision.get("action", "")
            data = decision.get("data", {})

            # Bypass: if AI used "query" but user asks about stored data → force read_file
            if action == "query":
                msg_lower = msg.lower()
                if any(w in msg_lower for w in ["задач", "завдан", "справ", "нагадуван", "remind", "task"]):
                    action = "read_file"
                    decision["action"] = "read_file"
                    decision["target"] = {"folder": "Zefirka", "filename": "tasks.md"}
                elif any(w in msg_lower for w in ["бюджет", "витрат", "фінанс", "грош", "budget", "expense"]):
                    action = "read_file"
                    decision["action"] = "read_file"
                    decision["target"] = {"folder": "Zefirka", "filename": "finances.md"}
                elif any(w in msg_lower for w in ["проект", "project"]):
                    action = "read_file"
                    decision["action"] = "read_file"
                    decision["target"] = {"folder": "Zefirka", "filename": "projects.md"}
                elif any(w in msg_lower for w in ["погод", "weather"]):
                    action = "get_weather"
                    decision["action"] = "get_weather"

            if action == "query" and decision.get("response", "").startswith("Зараз перевірю"):
                decision["response"] = "На жаль, я не можу знайти цю інформацію. Спробуй уточнити запит."

            success, result = self.engine.execute(decision)

            # read_file → re-ask AI
            if action == "read_file":
                if success and result.startswith(FILE_CONTENT_MARKER):
                    parts = result.split(":", 2)
                    file_path = parts[1]
                    file_content = parts[2]
                    analysis = self.deepseek.analyze_request(
                        f"User asked: {msg}\n\nFile ({file_path}):\n{file_content[:3000]}\n\nAnalyze and respond.",
                        self.router.get_routing_guide(),
                        self.context.get_conversation_context(),
                        self.language,
                    )
                    final = analysis.get("response", result)[:4096]
                else:
                    file_path = decision.get("target", {}).get("filename", "?")
                    analysis = self.deepseek.analyze_request(
                        f"User asked: {msg}\n\nFile '{file_path}' was not found (vault is empty). "
                        f"Respond to the user in {self.language} with a friendly message that "
                        f"there is no data yet, and offer to create it.",
                        self.router.get_routing_guide(),
                        self.context.get_conversation_context(),
                        self.language,
                    )
                    final = analysis.get("response", result)[:4096]
                await update.message.reply_text(_md_to_html(final), parse_mode="HTML")
                self.context.add_to_history("bot", final)
                self.context.add_action("read_file", file_path, success)
                self.action_log.log("read_file", file_path, True)
                return

            # fetch_url → re-ask AI with content
            if action == "fetch_url" and success and result.startswith(URL_CONTENT_MARKER):
                parts = result.split(":", 2)
                url = parts[1]
                content = parts[2]
                analysis = self.deepseek.analyze_request(
                    f"User asked: {msg}\n\nURL ({url}):\n{content[:3500]}\n\nAnalyze/summarize.",
                    self.router.get_routing_guide(),
                    self.context.get_conversation_context(),
                    self.language,
                )
                final = analysis.get("response", result)[:4096]
                await update.message.reply_text(_md_to_html(final), parse_mode="HTML")
                self.context.add_to_history("bot", final)
                self.context.add_action("fetch_url", url, True)
                self.action_log.log("fetch_url", url, True)
                return

            if success:
                ai_resp = decision.get("response", "")
                if action in ("query", "reflection", "help"):
                    final = ai_resp or result
                elif action == "complete_task":
                    final = result
                else:
                    action_msg = re.sub(r"[✅❌📝💰🚀🗑]", "", result).strip()
                    final = f"{ai_resp}\n\n{action_msg}" if ai_resp else action_msg
            else:
                final = f"❌ {result}"

            final = _md_to_html(final[:4096])
            buttons = _buttons_for(action, data)
            await update.message.reply_text(final, parse_mode="HTML", reply_markup=buttons)
            self.context.add_to_history("bot", final)
            self.context.add_action(action, str(decision.get("target", {})), success)
            self.action_log.log(action, str(decision.get("target", {})), success, decision.get("reasoning", ""))
            logger.info(f"Done: {action} {'OK' if success else 'FAIL'}")

        except Exception as e:
            logger.error(f"Handler error: {e}")
            await update.message.reply_text(f"❌ {e}")
