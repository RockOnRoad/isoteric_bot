"""Main entry point for the Aiogram bot."""

import asyncio
import logging
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from db.database import engine
from db.models import Base
from routers import router
from core.config import settings, bot
from middlewares import DatabaseMiddleware
from services import PaymentPoller, WebhookServer

logger = logging.getLogger(__name__)


async def init_database() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        # await conn.run_sync(Base.metadata.create_all)
        pass


COMMANDS = [
    BotCommand(command="start", description="Открыть себя"),
    # BotCommand(command="help", description="Подсказки"),
]


async def main() -> None:
    """Main application entry point."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="\n--- %(levelname)s: %(asctime)s - %(name)s ---\n%(message)s",
    )
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Validate required settings
    if not settings.token:
        logger.error(
            "BOT_TOKEN is required but not set. "
            "Please set it in your .env file or environment variables."
        )
        raise ValueError("BOT_TOKEN is required")

    # Initialize database
    logger.info("Initializing database...")
    await init_database()
    logger.info("Database initialized.")

    # # Initialize payment poller
    # payment_poller = PaymentPoller()
    # await payment_poller.start()
    # logger.info("Payment poller started.")

    # Initialize webhook listener for YooKassa
    webhook_server = WebhookServer(port=8443, bot=bot)
    await webhook_server.start()
    logger.info("Webhook server started.")

    # Initialize dispatcher
    dp = Dispatcher()
    dp.update.outer_middleware(DatabaseMiddleware())

    # Register routers
    dp.include_router(router)

    logger.info("Bot started. Press Ctrl+C to stop.")
    await bot.set_my_commands(commands=COMMANDS)
    await bot.delete_webhook(drop_pending_updates=True)
    # Start polling
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    finally:
        # await payment_poller.stop()  # Останавливаем опрос при завершении
        await webhook_server.stop()
        await bot.session.close()
        await dp.fsm.storage.close()


if __name__ == "__main__":
    asyncio.run(main())
