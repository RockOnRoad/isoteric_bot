import logging
from aiogram.filters import CommandObject
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from db.crud import upsert_user, add_entry_to_user_sources


logger = logging.getLogger(__name__)


async def first_start_routine(
    command: CommandObject, message: Message, db_session: AsyncSession
):
    """
    Обрабатывает логику первого запуска бота: создание/обновление пользователя,
    обработка реферера и пригласительной ссылки.

    Args:
        command: Объект команды с аргументами
        message: Сообщение от пользователя
        db_session: Сессия базы данных
    """
    logger.info(
        f"{message.from_user.id} @{message.from_user.username} - 'first_start_routine'"
    )

    referrer = None
    if command.args:
        #  Собираем payload команды start
        source = command.args.split("_")[0]

        #  Добавляем реферера, ежели таковой имеется
        if source == "ref":
            try:
                referrer = int(command.args.split("_")[1])
            except AttributeError:
                logger.error(f"Ref. link has no referrer id (ref_...)")
                return

    try:
        user = await upsert_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            referred_id=referrer,
            session=db_session,
        )
    except IntegrityError:
        return None

    if command.args:
        #  Добавляем источник прихода пользователя
        await add_entry_to_user_sources(
            user_id=user.id, source=command.args, session=db_session
        )

    return user
