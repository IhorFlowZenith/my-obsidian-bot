"""Main Bot Class — runs polling + background scheduler"""

import asyncio
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler as TCH,
    MessageHandler as TMH, CallbackQueryHandler,
    filters,
)

from src.config import get_config
from src.logger import setup_logger
from src.handlers import CommandHandler, MessageHandler
from src.services.scheduler import BotScheduler
from src.services.github_service import GitHubService

logger = setup_logger(__name__)
config = get_config()


class ZefirkaBot:
    def __init__(self):
        self.config = config
        self.language = config.USER_LANGUAGE
        self.command_handler = CommandHandler(self.language)
        self.message_handler = MessageHandler(self.language)
        self.scheduler: BotScheduler = None
        self.app = None
        self.github = GitHubService()

    def setup_handlers(self):
        logger.info("Setting up handlers...")
        self.app.add_handler(TCH("start", self.command_handler.start))
        self.app.add_handler(TCH("help", self.command_handler.help))
        self.app.add_handler(TCH("tasks", self.command_handler.tasks))
        self.app.add_handler(TCH("budget", self.command_handler.budget))
        self.app.add_handler(TCH("projects", self.command_handler.projects))
        self.app.add_handler(TMH(filters.TEXT & ~filters.COMMAND, self.message_handler.handle))
        self.app.add_handler(CallbackQueryHandler(self._button_callback))
        logger.info("Handlers setup complete")

    async def _button_callback(self, update: Update, context):
        query = update.callback_query
        await query.answer()
        data = query.data
        uid = update.effective_user.id
        if config.ALLOWED_USER_ID and uid != config.ALLOWED_USER_ID:
            return

        # done:task_name
        if data.startswith("done:"):
            title = data[5:]
            msg = self.message_handler.context.get_conversation_context()
            self.github.read_file_content("Zefirka/tasks.md")
            lines = self.github.read_file_content("Zefirka/tasks.md").split("\n")
            for i, line in enumerate(lines):
                if line.strip().startswith("- [ ]") and title.lower() in line.lower():
                    lines[i] = line.replace("- [ ]", "- [x]", 1)
                    break
            sha = (self.github.get_file("Zefirka/tasks.md") or {}).get("sha")
            ok = self.github.create_or_update_file("Zefirka/tasks.md", "\n".join(lines), f"Done: {title}", sha=sha)
            await query.edit_message_text(f"✅ <b>{title}</b> — виконано!", parse_mode="HTML")

        # delete:task_name
        elif data.startswith("delete:"):
            title = data[7:]
            lines = self.github.read_file_content("Zefirka/tasks.md").split("\n")
            lines = [l for l in lines if not (l.strip().startswith("- [") and title.lower() in l.lower())]
            sha = (self.github.get_file("Zefirka/tasks.md") or {}).get("sha")
            self.github.create_or_update_file("Zefirka/tasks.md", "\n".join(lines), f"Deleted: {title}", sha=sha)
            await query.edit_message_text(f"🗑 <b>{title}</b> — видалено!", parse_mode="HTML")

    async def run(self):
        logger.info(f"Starting {config.BOT_NAME}...")
        self.app = Application.builder().token(config.TELEGRAM_TOKEN).build()
        self.setup_handlers()

        self.scheduler = BotScheduler(self.app.bot)
        self.message_handler.set_scheduler(self.scheduler)

        logger.info(f"🤖 {config.BOT_NAME} started!")
        async with self.app:
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            logger.info("Bot is polling...")

            scheduler_task = asyncio.create_task(self.scheduler.run())

            try:
                await asyncio.Future()
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                scheduler_task.cancel()
            finally:
                await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()
