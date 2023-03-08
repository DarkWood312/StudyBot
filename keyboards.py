from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup

async def cancel_markup():
    markup = InlineKeyboardMarkup()
    cancel_button = InlineKeyboardButton('Отмена', callback_data='cancel')
    markup.add(cancel_button)
    return markup