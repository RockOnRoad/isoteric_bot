from typing import Any

from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup
from aiogram.types.reply_keyboard_markup import ReplyKeyboardMarkup
from aiogram.filters.callback_data import CallbackData


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


class InlineKeyboard:
    """Inline keyboard builder for multiple buttons with callback data or url.

    Args:
        buttons: List of dictionaries with keys that correspond to the button parameters.
        width: Width of the keyboard.
        include_cancel: Whether to include a cancel button.

    Keys:
        text: Visible text of the button.
        callback_data: Callback data of the button.
            Example:
            ``` python
            from aiogram.filters.callback_data import CallbackData

            class EditBio(CallbackData, prefix="edit_bio"):
                button: str

            buttons: tuple[dict[str, CallbackData | str]] = (
                {"text": "Edit", "callback_data": EditBio(button="user.id")},
                {"text": "Cancel", "callback_data": EditBio(button="cango_back")},
            )
            kbd = InlineKbd(buttons=buttons, width=2)
            await message.answer("Inline keyboard", reply_markup=kbd.markup)

            ```
        url: URL of the button.
    """

    def __init__(
        self,
        buttons: list[dict[str, CallbackData | str]],
        width: int = 2,
        include_cancel: bool = False,
    ):
        self.buttons = buttons
        self.width = width
        self.include_cancel = include_cancel

    @property
    def markup(self) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()

        for obj in self.buttons:
            if "callback_data" in obj:
                obj["callback_data"] = obj["callback_data"].pack()
            kb.button(**obj)
            # # Не мутируем исходный объект, иначе при повторном вызове pack получим ошибку
            # kwargs = obj.copy()
            # if "callback_data" in kwargs and isinstance(
            #     kwargs["callback_data"], CallbackData
            # ):
            #     kwargs["callback_data"] = kwargs["callback_data"].pack()
            # kb.button(**kwargs)

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
