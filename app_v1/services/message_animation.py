import asyncio
import logging
from time import time

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery

logger = logging.getLogger(__name__)


class MessageAnimation:
    """Класс для анимации сообщений с меняющимися точками."""

    def __init__(
        self,
        message_or_call: Message | CallbackQuery,
        base_text: str,
        dots: list[str] | None = None,
        interval: float = 0.4,
        timeout: float | None = 60.0,
    ):
        """
        Инициализация анимации сообщения.

        Args:
            message_or_call: Сообщение для анимации или CallbackQuery для создания нового сообщения.
            base_text: Базовый текст сообщения (без точек).
            dots: Список вариантов точек. По умолчанию [".", "..", "..."].
            interval: Интервал обновления в секундах. По умолчанию 0.4.
            timeout: Максимальное время работы анимации в секундах. По умолчанию 30.0. None отключает таймаут.
        """
        self.message_or_call = message_or_call
        self.message: Message | None = None
        self.base_text = base_text
        self.dots = dots or [".", "..", "..."]
        self.interval = interval
        self.timeout = timeout
        self.animation_stop = asyncio.Event()
        self.animation_task: asyncio.Task | None = None

    async def _animate(
        self,
    ) -> None:
        """Внутренний метод для анимации сообщения."""
        dot_index = 0
        first_update = True
        start_time = time()

        while not self.animation_stop.is_set():
            try:
                elapsed_time = time() - start_time
                if elapsed_time >= self.timeout:
                    logger.warning(
                        f"Animation timeout reached ({self.timeout}s), stopping animation"
                    )
                    await self.message.delete()
                    await bot.send_message(
                        chat_id=self.message_or_call.from_user.id,
                        text="Операция заняла слишком много времени",  # Тут надо прервать выполнение основной задачи
                    )
                    raise TimeoutError

                text = f"{self.base_text}{self.dots[dot_index]}"

                if first_update:
                    # Создаем сообщение при первом обновлении
                    try:
                        self.message = await bot.send_message(
                            chat_id=self.message_or_call.from_user.id, text=text
                        )
                    except TelegramBadRequest as e:
                        logger.error(f"Error sending first animation message: {e}")
                        break
                    first_update = False

                dot_index = (dot_index + 1) % len(self.dots)
                await asyncio.sleep(self.interval)

                # Обновляем существующее сообщение
                try:
                    await self.message.edit_text(text)
                except TelegramBadRequest:
                    continue
            except Exception as e:
                logger.error(f"Error animating message: {e}")
                break

    async def start(self) -> None:
        """Запускает анимацию сообщения."""
        if self.animation_task is None or self.animation_task.done():
            self.animation_stop.clear()
            self.animation_task = asyncio.create_task(self._animate())

    async def stop(self, delete_message: bool = True) -> None:
        """
        Останавливает анимацию сообщения.

        Args:
            delete_message: Если True, удаляет сообщение после остановки анимации.
        """
        self.animation_stop.set()
        if self.animation_task and not self.animation_task.done():
            self.animation_task.cancel()
            try:
                await self.animation_task
            except asyncio.CancelledError:
                pass

        if delete_message and self.message:
            try:
                await self.message.delete()
            except TelegramBadRequest:
                # Сообщение уже было удалено
                pass
            except Exception as e:
                logger.error(f"Error deleting message: {e}")

    async def __aenter__(self):
        """Поддержка контекстного менеджера - вход."""
        self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Поддержка контекстного менеджера - выход."""
        await self.stop()
