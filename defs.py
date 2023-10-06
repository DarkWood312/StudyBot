import _io
import io

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode, Message, ReplyKeyboardMarkup, KeyboardButton

from emoji import emojize

from random import shuffle

import db
from config import sql
from keyboards import menu_markup


async def modern_gdz_sender(user_id, var, gdz, message, subject_name: str, tem=None, work=None):
    if '-' in str(var):
        f, s = str(var).split('-')
        vars_list = [*range(int(f.strip()), int(s.strip()) + 1)]
    elif ',' in str(var):
        vars_list = str(var).split(',')
        vars_list = list(dict.fromkeys([int(i.strip()) for i in vars_list]))
    else:
        vars_list = [int(var)]
    for one_var in vars_list:
        if (tem is not None) and (work is not None):
            response, link = await gdz(tem, work, one_var)
        elif tem is not None:
            response, link = await gdz(str(tem), str(one_var))
        else:
            response, link = await gdz(one_var)
        response[0] = await modern_gdz_process(user_id, response[0])
        for group in response:
            if isinstance(group, str):
                await message.answer(group, parse_mode=ParseMode.HTML)
            else:
                if (tem is not None) and (work is not None):
                    group[0][
                        'caption'] = f'<b>{subject_name}</b>: <a href="{link}">Тема {tem}, Работа {work}, Вариант {one_var}</a>'
                elif tem is not None:
                    group[0][
                        'caption'] = f'<b>{subject_name}</b>: <a href="{link}">Параграф {tem}, Задание {one_var}</a>'
                else:
                    group[0]['caption'] = f'<b>{subject_name}</b>: <a href="{link}">{one_var}</a>'
                group[0]['parse_mode'] = ParseMode.HTML
                await message.answer_media_group(group)


async def modern_gdz_process(user_id, arr, doc: bool = None):
    if not isinstance(arr, list):
        sep = 4096
        l = arr
    else:
        if doc is None:
            doc = bool(await sql.get_data(user_id, 'upscaled'))
        sep = 10
        if doc:
            l = [types.InputMediaDocument(i) for i in arr]
        else:
            l = [types.InputMediaPhoto(i) for i in arr]
    return [l[i:i + sep] for i in range(0, len(l), sep)]


async def orthoepy_word_formatting(words: list, pos: int):
    """
    PARSEMODE.HTML !!!
    """
    word = ''
    for letter in words[pos]:
        if letter.lower() in db.gl:
            letter = f'<b>{letter}</b>'
        word = word + letter
    output = f'<code>{pos + 1}/{len(words)})</code> {word.upper()}'
    return output


async def cancel_state(state: FSMContext):
    state_ = await state.get_state()
    if state_ is not None:
        await state.finish()


async def main_message(message: Message):
    await message.answer(db.gdz_help_non_gdz, parse_mode=ParseMode.HTML,
                         reply_markup=await menu_markup(message))
