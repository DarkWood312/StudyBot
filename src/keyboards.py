from typing import List

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from emoji import emojize

from config import sql


async def menu_markup(user_id):
    markup = ReplyKeyboardBuilder()
    compress_button = KeyboardButton(text=emojize(f'Сжатие изображений - {":cross_mark:" if await sql.get_data(user_id, "upscaled") == 1 else ":check_mark_button:"}'))
    ai_button = KeyboardButton(text='AI🧠🔟')
    markup.row(compress_button)
    if await sql.get_data(user_id, 'ai_access'):
        markup.row(ai_button)
    return markup.as_markup(resize_keyboard=True)


async def ai_markup():
    markup = ReplyKeyboardBuilder()
    chatgpt_turbo_button = KeyboardButton(text='ChatGPT-Turbo💬->💬')
    midjourney_v4_button = KeyboardButton(text='Midjourney-V4💬->🦋')
    playground_v2_button = KeyboardButton(text='Playground-V2💬->🦋')
    stable_diffusion_xl_turbo_button = KeyboardButton(text='Stable Diffusion XL Turbo💬->🦋')
    gemini_pro_button = KeyboardButton(text='Gemini-Pro(💬|🦋)->💬')
    claude_button = KeyboardButton(text='Claude💬->💬')
    mistral_medium_button = KeyboardButton(text='Mistral Medium💬->💬')
    dalle3_button = KeyboardButton(text='Dall-E 3💬->🦋')
    markup.row(chatgpt_turbo_button, gemini_pro_button)
    markup.row(claude_button, mistral_medium_button)
    markup.row(midjourney_v4_button, playground_v2_button)
    markup.row(stable_diffusion_xl_turbo_button, dalle3_button)
    markup.row(KeyboardButton(text='Отмена❌'))
    return markup.as_markup(resize_keyboard=True, one_time_keyboard=True)



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
