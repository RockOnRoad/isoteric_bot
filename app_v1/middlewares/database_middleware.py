"""Database session middleware."""

from typing import Callable, Awaitable, Dict, Any
import logging
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from db.database import AsyncSessionLocal


logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    """Middleware to inject database session into context."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Inject database session into context."""
        async with AsyncSessionLocal() as session:
            data["db_session"] = session
            try:
                # Execute handler and wait for it to complete
                result = await handler(event, data)
                return result
            except (DBAPIError, SQLAlchemyError) as e:
                # Rollback on database errors
                try:
                    await session.rollback()
                except Exception as rollback_error:
                    logger.exception(f"Error rolling back session: {rollback_error}")
                logger.exception(f"Database error in handler: {e}")
                raise
            except Exception as e:
                # For other errors, try to rollback if there are pending changes
                # Rollback is safe even if there's no active transaction
                try:
                    await session.rollback()
                except Exception as rollback_error:
                    logger.exception(f"Error rolling back session: {rollback_error}")
                raise
