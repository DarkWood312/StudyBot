from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from emoji import emojize

from config import sql


async def menu_markup(message):
    return ReplyKeyboardMarkup(resize_keyboard=True).add(
        KeyboardButton(emojize(
            f'Сжатие - {":cross_mark:" if await sql.get_data(message.from_user.id, "upscaled") == 1 else ":check_mark_button:"}')))

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
