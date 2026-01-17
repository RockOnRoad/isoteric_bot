import logging
from math import e
from aiogram.filters import CommandObject
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from db.crud import (
    upsert_user,
    add_entry_to_user_sources,
    get_user,
    get_last_added_user_id,
)


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
    referrer_id = None
    sources: list[tuple[str, str]] = []

    # Сначала вытаскиваем реферера и остальные параметры из payload
    if command.args:
        source_parts = command.args.split("_")
        referrer = ""
        for key, value in zip(source_parts[::2], source_parts[1::2]):
            if key == "ref":
                #  Если реферер уже был найден, то пропускаем
                if referrer:
                    continue
                #  Если это первая пара с ключом "ref", сохраняем реферера
                else:
                    try:
                        referrer = int(value)
                    except (TypeError, ValueError):
                        logger.warning("Invalid ref: %s", value)
                        continue
                    #  Проверяем, что пользователь не ввёл сам себя в качестве реферера
                    last_added_user_id = await get_last_added_user_id(db_session)
                    if last_added_user_id:
                        current_user = last_added_user_id + 1
                    #  Если это самый первый пользователь
                    else:
                        current_user = 1
                    if referrer != current_user:
                        #  Проверяем, что реферер существует
                        user_by_ref = await get_user(referrer, db_session)
                        if not user_by_ref:
                            logger.info("Referrer %s not found", referrer)
                            continue
                        #  Сохраняем реферера
                        referrer_id = referrer
                    continue

            sources.append((str(key), str(value)))

    try:
        user = await upsert_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            referred_id=referrer_id,
            session=db_session,
        )
    except IntegrityError:
        return None

    # Добавляем источники (коммитим один раз в конце, если есть что писать)
    if sources:
        for key, value in sources:
            await add_entry_to_user_sources(
                user_id=user.id,
                source_key=key,
                source_value=value,
                session=db_session,
                commit=False,
            )
        await db_session.commit()

    return user
