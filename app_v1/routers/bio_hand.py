"""User command handlers."""

from datetime import datetime, timedelta
import logging
import xml.sax.saxutils as saxutils

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from keyboards import InlineKbd
from schemas import BioStates, BioEdit, BioCorrect, BioSex


logger = logging.getLogger(__name__)
bio_rtr = Router()


async def summary_message(message: Message, state: FSMContext) -> None:
    name = await state.get_value("name")
    birthday = await state.get_value("birthday")
    edited = await state.get_value("edited")

    msg = f"{saxutils.escape(name)}, данные успешно обновлены.\n" if edited else ""

    msg = msg + (
        "Проверяю настройки твоей энергии… ⏳\n"
        f"Твоё имя:  {saxutils.escape(name)}\n"
        f"Твой день рождения: <b>{birthday}</b>\n"
        "Всё верно? Или нужно что-то скорректировать?"
    )

    main_buttons = {
        "📝 Изменить Имя": BioEdit(button="name").pack(),
        "📆 Изменить Дату": BioEdit(button="birthday").pack(),
        "✅  Да, считать": BioCorrect(button="yes").pack(),
    }
    kbd = InlineKbd(buttons=main_buttons, width=2)

    await state.set_state(BioStates.edit_or_confirm)
    await state.update_data(edited=False)

    await message.answer(msg, reply_markup=kbd.markup)


#  ----------- NAME ----------- ШАГ 1


#  workflow name
@bio_rtr.message(BioStates.name)
async def handle_name_message(message: Message, state: FSMContext) -> None:

    name = saxutils.escape(message.text)
    await state.update_data(name=message.text)

    msg = (
        f"Приятно познакомиться, {name} ✨\n"
        """Чтобы трактовки были максимально точными и живыми, мне важно учитывать твою энергетику — мягкий женский поток или структурный мужской. Энергии Матрицы по-разному проявляются в мужском и женском полюсе.
<b>Укажи, пожалуйста, свой пол 👇</b>"""
    )
    sex_buttons = {
        "👩 Женский": BioSex(sex="f").pack(),
        "👨 Мужской": BioSex(sex="m").pack(),
    }
    kbd = InlineKbd(buttons=sex_buttons, width=2)

    await state.set_state(BioStates.sex)
    await message.answer(msg, reply_markup=kbd.markup)


#  ----------- SEX ----------- ШАГ 2


@bio_rtr.callback_query(BioSex.filter(), BioStates.sex)
async def handle_birthday_message(
    call: CallbackQuery, callback_data: BioSex, state: FSMContext
) -> None:

    await state.update_data(sex=callback_data.sex)
    await state.update_data(birthday_counter=0)

    birthday = await state.get_value("birthday")
    msg = """Отлично, я зафиксировала твой пол 🌿
Теперь перейдём к твоему энергетическому коду.
Дата рождения — это матрица, с которой душа приходит в мир.
Напиши свою дату рождения в формате <b>ДД.ММ.ГГГГ</b>
Например: <b>17.04.1990</b>
    """

    await state.set_state(BioStates.birthday)
    await call.message.edit_text(msg)


@bio_rtr.callback_query(
    BioEdit.filter(F.button == "birthday"), BioStates.edit_or_confirm
)
async def edit_birthday_callback(call: CallbackQuery, state: FSMContext) -> None:

    await state.update_data(birthday_counter=0)
    await state.update_data(edited=True)

    msg = (
        f"<b>Обновляю дату рождения. 🔢</b>\n"
        "Введи новую дату строго в формате <b>ДД.ММ.ГГГГ.</b>\n"
        "Я пересчитаю твою Матрицу. (Пример: 15.08.1987)"
    )

    await state.set_state(BioStates.birthday)
    await call.message.edit_text(msg)


#  ----------- BIRTHDAY ----------- ШАГ 3


def date_in_future_or_distant_past(date: str) -> bool:
    today = datetime.now().date()
    birth_date = datetime.strptime(date, "%d.%m.%Y").date()

    if birth_date > today:
        return True
    elif birth_date < today - timedelta(days=365 * 100):
        return True
    else:
        return False


def correct_date_format(date: str) -> bool:
    try:
        datetime.strptime(date, "%d.%m.%Y")
        return True
    except ValueError:
        return False


@bio_rtr.message(BioStates.birthday)
async def birthday_message(message: Message, state: FSMContext) -> None:

    birthday_counter = await state.get_value("birthday_counter")

    if not correct_date_format(date=message.text):
        if birthday_counter < 1:
            msg = """Кажется, формат немного сбился 😊
Пожалуйста, используй только цифры и точки.
Например: <b>05.05.1995</b>
        """
        else:
            msg = """Хочу рассчитать всё точно, поэтому мне важно получить корректную дату 🌿
Пожалуйста, вводи её только цифрами, вот так:
<b>07.11.1992</b>"""
        await state.update_data(birthday_counter=birthday_counter + 1)

    elif date_in_future_or_distant_past(date=message.text):
        msg = """Матрица не читает даты вне человеческой жизни ✨
Пожалуйста, введи реальную дату рождения.
Например: <b>05.05.1995</b>
        """
    else:
        await state.update_data(birthday=message.text)
        await summary_message(message, state)

        return
    await message.answer(msg)


#  ----------- EDIT NAME -----------


#  edit name
@bio_rtr.callback_query(BioEdit.filter(F.button == "name"), BioStates.edit_or_confirm)
async def edit_name_callback(call: CallbackQuery, state: FSMContext) -> None:

    msg = """<b>Обновляю имя. 📝</b>
Пожалуйста, введи новое имя, и я мгновенно обновлю его в твоем профиле. (Просто напиши новое имя в чат 👇)"""

    await state.set_state(BioStates.edit_name)
    await call.message.edit_text(msg)


#  edit name
@bio_rtr.message(BioStates.edit_name)
async def handle_edit_name_message(message: Message, state: FSMContext) -> None:

    await state.update_data(name=message.text)
    await state.update_data(edited=True)

    await summary_message(message, state)
    return
