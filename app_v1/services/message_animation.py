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

    async def _animate(self) -> None:
        """Внутренний метод для анимации сообщения."""
        dot_index = 0
        first_update = True
        start_time = time()

        while not self.animation_stop.is_set():
            try:
                # Проверяем таймаут
                if self.timeout is not None:
                    elapsed_time = time() - start_time
                    if elapsed_time >= self.timeout:
                        logger.warning(
                            f"Animation timeout reached ({self.timeout}s), stopping animation"
                        )
                        # Отправляем сообщение об ошибке
                        error_text = "Во время создания образа произошла ошибка. Энергия не будет списана."
                        if self.message:
                            try:
                                await self.message.edit_text(error_text)
                            except TelegramBadRequest:
                                # Если не удалось отредактировать, отправляем новое сообщение
                                if isinstance(self.message_or_call, CallbackQuery):
                                    await self.message_or_call.message.answer(
                                        error_text
                                    )
                                elif isinstance(self.message_or_call, Message):
                                    await self.message_or_call.answer(error_text)
                        else:
                            # Если сообщение еще не создано, создаем новое
                            if isinstance(self.message_or_call, CallbackQuery):
                                await self.message_or_call.message.answer(error_text)
                            elif isinstance(self.message_or_call, Message):
                                await self.message_or_call.answer(error_text)
                        return

                text = f"{self.base_text}{self.dots[dot_index]}"

                if first_update:
                    # Создаем сообщение при первом обновлении
                    if isinstance(self.message_or_call, CallbackQuery):
                        try:
                            # Пытаемся отредактировать сообщение, убирая кнопки
                            # Важно: reply_markup=None обязательно для сообщений с кнопками
                            self.message = await self.message_or_call.message.edit_text(
                                text
                            )
                        except TelegramBadRequest as e:
                            # Если не удалось отредактировать, создаем новое сообщение
                            logger.warning(f"Could not edit message, creating new: {e}")
                            self.message = await self.message_or_call.message.answer(
                                text
                            )
                    else:
                        # Если уже есть сообщение, используем его
                        self.message = self.message_or_call
                        await self.message.edit_text(text)
                    first_update = False
                else:
                    # Обновляем существующее сообщение
                    if self.message:
                        await self.message.edit_text(text)

                dot_index = (dot_index + 1) % len(self.dots)
                await asyncio.sleep(self.interval)
            except TelegramBadRequest:
                # Сообщение было удалено или изменено
                break
            except Exception as e:
                logger.error(f"Error animating message: {e}")
                break

    def start(self) -> None:
        """Запускает анимацию сообщения."""
        if self.animation_task is None or self.animation_task.done():
            self.animation_stop.clear()
            self.animation_task = asyncio.create_task(self._animate())

    async def stop(self, delete_message: bool = False) -> None:
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
