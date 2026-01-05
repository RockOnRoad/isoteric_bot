from typing import Any

from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup
from aiogram.types.reply_keyboard_markup import ReplyKeyboardMarkup


class InlineKbd:
    def __init__(
        self, buttons: dict[str, Any], width: int = 2, include_cancel: bool = False
    ):
        self.buttons = buttons
        self.width = width
        self.include_cancel = include_cancel

    @property
    def markup(self) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()

        for text, data in self.buttons.items():
            kb.button(text=text, callback_data=str(data))

        if self.include_cancel:
            kb.button(text="✖️ Отмена", callback_data="cancel")
        kb.adjust(self.width)
        return kb.as_markup()


class ReplyKbd:
    def __init__(self, buttons: tuple, width: int = 2, include_cancel: bool = False):
        self.buttons = buttons
        self.width = width
        self.include_cancel = include_cancel

    @property
    def markup(self) -> ReplyKeyboardMarkup:
        kb = ReplyKeyboardBuilder()

        for text in self.buttons:
            kb.button(text=text)

        kb.adjust(self.width)
        return kb.as_markup(resize_keyboard=True)
