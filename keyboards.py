from typing import List

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from emoji import emojize

from config import sql


async def menu_markup(user_id):
    button = KeyboardButton(text=emojize(f'Сжатие - {":cross_mark:" if await sql.get_data(user_id, "upscaled") == 1 else ":check_mark_button:"}'))
    markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[button]])
    return markup


async def cancel_markup():
    markup = InlineKeyboardBuilder()
    cancel_button = InlineKeyboardButton(text='Отмена', callback_data='cancel')
    markup.add(cancel_button)
    return markup.as_markup()


async def reply_cancel_markup():
    cancel_button = KeyboardButton(text='Закончить❌')
    markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[cancel_button]])
    return markup


async def orthoepy_word_markup(gls: List[str]):
    markup = InlineKeyboardBuilder()
    for gl in range(1, len(gls) + 1):
        gl = str(gl)
        markup.add(InlineKeyboardButton(text=f'{gl}. {gls[int(gl)-1].upper()}', callback_data=gl))
    return markup.as_markup()
