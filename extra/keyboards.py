from typing import List

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, \
    Message
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from emoji import emojize

from extra.config import sql


async def menu_markup(user_id) -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardBuilder()
    compress_button = KeyboardButton(text=emojize(
        f'Сжатие изображений - {":cross_mark:" if await sql.get_data(user_id, "upscaled") == 1 else ":check_mark_button:"}'))
    ai_button = KeyboardButton(text='AI🧠🔟')
    wolfram_button = KeyboardButton(text='WolframAlpha📙')
    desmos_button = KeyboardButton(text='Графический калькулятор📊', web_app=WebAppInfo(url='https://tgbot.dwip.fun/'))
    uchus_button = KeyboardButton(text='Uchus.online🤓')
    markup.row(compress_button)
    markup.row(wolfram_button)
    markup.row(desmos_button)
    markup.row(uchus_button)
    if await sql.get_data(user_id, 'ai_access'):
        markup.row(ai_button)
    return markup.as_markup(resize_keyboard=True)


# async def ai_markup() -> ReplyKeyboardMarkup:
#     markup = ReplyKeyboardBuilder()
#     chatgpt_turbo_button = KeyboardButton(text='ChatGPT-Turbo💬->💬')
#     # midjourney_v4_button = KeyboardButton(text='Midjourney-V4💬->🦋')
#     midjourney_v6_button = KeyboardButton(text='Midjourney-V6💬->🦋')
#     kandinsky_button = KeyboardButton(text='Kandinsky💬->🦋')
#     playground_v2_button = KeyboardButton(text='Playground-V2💬->🦋')
#     stable_diffusion_xl_turbo_button = KeyboardButton(text='Stable Diffusion XL Turbo💬->🦋')
#     gemini_pro_button = KeyboardButton(text='Gemini-Pro(💬|🦋)->💬')
#     claude_button = KeyboardButton(text='Claude💬->💬')
#     gigachat_button = KeyboardButton(text='GigaChat💬->(💬|🦋)')
#     mistral_medium_button = KeyboardButton(text='Mistral Medium💬->💬')
#     # dalle3_button = KeyboardButton(text='Dall-E 3💬->🦋')
#     photomaker_button = KeyboardButton(text='Photomaker🦋->🦋')
#     hcrt_button = KeyboardButton(text='High-Resolution-Controlnet-Tile🦋->🦋')
#     markup.row(chatgpt_turbo_button, gemini_pro_button)
#     markup.row(gigachat_button)
#     markup.row(midjourney_v6_button, playground_v2_button)
#     markup.row(stable_diffusion_xl_turbo_button, photomaker_button)
#     markup.row(hcrt_button)
#     markup.row(KeyboardButton(text='Отмена❌'))
#     return markup.as_markup(resize_keyboard=True, one_time_keyboard=True)

async def visionai_markup() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardBuilder()
    llm = KeyboardButton(text='LLM models')
    dalle = KeyboardButton(text='Dalle')
    text2gif = KeyboardButton(text='Text2GIF')
    # sd = KeyboardButton(text='Stable Diffusion models')

    markup.row(llm, dalle)
    markup.row(text2gif)
    # markup.row(sd)
    markup.row(KeyboardButton(text='Отмена❌'))

    return markup.as_markup(resize_keyboard=True, one_time_keyboard=True)


async def cancel_markup() -> InlineKeyboardMarkup:
    markup = InlineKeyboardBuilder()
    cancel_button = InlineKeyboardButton(text='Отмена', callback_data='cancel')
    markup.add(cancel_button)
    return markup.as_markup()


async def reply_cancel_markup() -> ReplyKeyboardMarkup:
    cancel_button = KeyboardButton(text='Закончить❌')
    markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[cancel_button]])
    return markup


async def orthoepy_word_markup(gls: List[str]) -> InlineKeyboardMarkup:
    markup = InlineKeyboardBuilder()
    for gl in range(1, len(gls) + 1):
        gl = str(gl)
        markup.add(InlineKeyboardButton(text=f'{gl}. {gls[int(gl) - 1].upper()}', callback_data=gl))
    return markup.as_markup()


async def uchus_online_markup() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardBuilder()
    topics_button = KeyboardButton(text='Задания📓')
    settings_button = KeyboardButton(text='Настройки⚙️')
    markup.row(topics_button).row(settings_button).row(KeyboardButton(text='Закончить❌'))
    return markup.as_markup(resize_keyboard=True)


async def uchus_online_settings_markup(user_id: int) -> InlineKeyboardMarkup:
    table_data = await sql.get_uchus_settings(user_id)
    settings_markup = InlineKeyboardBuilder()
    settings_markup.row(
        InlineKeyboardButton(text=f'Диапазон сложности: {table_data.min_complexity}...{table_data.max_complexity}',
                             callback_data='uchuss_diff'))
    settings_markup.row(
        InlineKeyboardButton(text=f'Сложность: {"↗️" if table_data.complexity_asc else "↘️"}',
                             callback_data='uchuss_complexity'))

    return settings_markup.as_markup()
