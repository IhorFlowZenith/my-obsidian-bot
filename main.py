#!/usr/bin/env python3
"""
Zefirka - Smart Daily Assistant Bot
Entry point for the application
"""

import asyncio
import sys

from src.bot import ZefirkaBot
from src.config import get_config
from src.logger import setup_logger

logger = setup_logger(__name__)
config = get_config()


async def main():
    """Main entry point"""
    
    # Validate configuration
    if not all([config.TELEGRAM_TOKEN, config.DEEPSEEK_API_KEY, config.GITHUB_TOKEN]):
        logger.error("❌ Missing required environment variables!")
        logger.error("Required: TELEGRAM_TOKEN, DEEPSEEK_API_KEY, GITHUB_TOKEN")
        sys.exit(1)
    
    logger.info(f"Starting {config.BOT_NAME}...")
    logger.info(f"Language: {config.USER_LANGUAGE}")
    logger.info(f"Timezone: {config.USER_TIMEZONE}")
    
    # Create and run bot
    bot = ZefirkaBot()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
