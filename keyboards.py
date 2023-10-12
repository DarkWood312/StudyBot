from typing import List

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from emoji import emojize

from config import sql


async def menu_markup(user_id):
    return ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton(emojize(
            f'Сжатие - {":cross_mark:" if await sql.get_data(user_id, "upscaled") == 1 else ":check_mark_button:"}')))


async def cancel_markup():
    markup = InlineKeyboardMarkup()
    cancel_button = InlineKeyboardButton('Отмена', callback_data='cancel')
    markup.add(cancel_button)
    return markup


async def reply_cancel_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    cancel_button = KeyboardButton('Закончить❌')
    markup.add(cancel_button)
    return markup


async def orthoepy_word_markup(gls: List[str]):
    markup = InlineKeyboardMarkup()
    for gl in range(1, len(gls) + 1):
        gl = str(gl)
        markup.add(InlineKeyboardButton(f'{gl}. {gls[int(gl)-1].upper()}', callback_data=gl))
    return markup
