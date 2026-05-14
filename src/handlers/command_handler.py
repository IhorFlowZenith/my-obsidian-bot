"""Command Handler - Handles Telegram commands"""

from telegram import Update
from telegram.ext import ContextTypes

from src.config import get_config
from src.logger import setup_logger
from src.services.github_service import GitHubService

logger = setup_logger(__name__)
config = get_config()

MESSAGES = {
    "uk": {
        "start": f"🧁 {config.BOT_NAME} - Твій розумний помічник\n\n"
                 f"Привіт! Я допоможу тобі керувати:\n"
                 f"📋 Задачами\n"
                 f"💰 Витратами\n"
                 f"🚀 Проектами\n"
                 f"📊 Аналізом дня\n\n"
                 f"Напиши /help для деталей",
        "help": "Команди:\n"
                "/tasks — список задач\n"
                "/budget — бюджет та витрати\n"
                "/projects — список проектів\n\n"
                "Або просто пиши будь-які запити!",
    },
    "en": {
        "start": f"🧁 {config.BOT_NAME} - Your Smart Assistant\n\n"
                 f"Hi! I'll help you manage:\n"
                 f"📋 Tasks\n"
                 f"💰 Expenses\n"
                 f"🚀 Projects\n"
                 f"📊 Daily Analysis\n\n"
                 f"Type /help for details",
        "help": "Commands:\n"
                "/tasks — task list\n"
                "/budget — budget & expenses\n"
                "/projects — project list\n\n"
                "Or just send any request!",
    },
    "ru": {
        "start": f"🧁 {config.BOT_NAME} - Твой умный помощник\n\n"
                 f"Привет! Я помогу тебе управлять:\n"
                 f"📋 Задачами\n"
                 f"💰 Расходами\n"
                 f"🚀 Проектами\n"
                 f"📊 Анализом дня\n\n"
                 f"Напиши /help для деталей",
        "help": "Команды:\n"
                "/tasks — список задач\n"
                "/budget — бюджет и расходы\n"
                "/projects — список проектов\n\n"
                "Или просто пиши любые запросы!",
    }
}


def _fmt(content: str, max_lines: int = 30) -> str:
    """Format file content as HTML"""
    if not content:
        return "<i>Файл порожній</i>"
    lines = content.split("\n")[:max_lines]
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped.lstrip("#").strip()
            tag = "b" if level <= 2 else "i"
            result.append(f"<{tag}>{text}</{tag}>")
        elif stripped.startswith("- [x]"):
            result.append(f"✅ {stripped[5:]}")
        elif stripped.startswith("- [ ]"):
            result.append(f"⬜ {stripped[5:]}")
        elif stripped.startswith("|"):
            result.append(stripped)
        else:
            result.append(stripped)
    return "\n".join(result)


class CommandHandler:
    def __init__(self, language: str = "uk"):
        self.language = language
        self.messages = MESSAGES.get(language, MESSAGES["en"])
        self.github = GitHubService()

    def _auth(self, uid: int) -> bool:
        allowed = config.ALLOWED_USER_ID
        return not allowed or uid == allowed

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not self._auth(uid):
            await update.message.reply_text("❌ Not authorized.")
            return
        await update.message.reply_text(self.messages["start"])

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not self._auth(uid):
            await update.message.reply_text("❌ Not authorized.")
            return
        await update.message.reply_text(self.messages["help"])

    async def tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not self._auth(uid):
            return
        content = self.github.read_file_content("Zefirka/tasks.md")
        text = f"<b>📋 Задачі</b>\n\n{_fmt(content)}" if content else "<b>📋</b> Немає задач"
        await update.message.reply_text(text, parse_mode="HTML")

    async def budget(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not self._auth(uid):
            return
        content = self.github.read_file_content("Zefirka/finances.md")
        text = f"<b>💰 Бюджет</b>\n\n{_fmt(content)}" if content else "<b>💰</b> Немає даних"
        await update.message.reply_text(text, parse_mode="HTML")

    async def projects(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        if not self._auth(uid):
            return
        content = self.github.read_file_content("Zefirka/projects.md")
        text = f"<b>🚀 Проекти</b>\n\n{_fmt(content)}" if content else "<b>🚀</b> Немає проектів"
        await update.message.reply_text(text, parse_mode="HTML")
