from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode, Message, ReplyKeyboardMarkup, KeyboardButton
from emoji import emojize

import db
from config import sql


async def gdz_sender(var, gdz, message, subject_name: str, tem=None, work=None):
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
        for group in response:
            if isinstance(group, str):
                await message.answer(group, parse_mode=ParseMode.HTML)
            else:
                if (tem is not None) and (work is not None):
                    group[0][
                        'caption'] = f'<b>{subject_name}</b>: <a href="{link}">Тема {tem}, Работа {work}, Вариант {one_var}</a>'
                elif tem is not None:
                    group[0]['caption'] = f'<b>{subject_name}</b>: <a href="{link}">Параграф {tem}, Задание {one_var}</a>'
                else:
                    group[0]['caption'] = f'<b>{subject_name}</b>: <a href="{link}">{one_var}</a>'
                group[0]['parse_mode'] = ParseMode.HTML
                await message.answer_media_group(group)


async def cancel_state(state: FSMContext):
    state_ = await state.get_state()
    if state_ is not None:
        await state.finish()


async def main_message(message: Message):
    await message.answer(db.gdz_help, parse_mode=ParseMode.HTML,
                         reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(
                             KeyboardButton(emojize(
                                 f'Сжатие - {":cross_mark:" if await sql.get_data(message.from_user.id, "upscaled") == 1 else ":check_mark_button:"}'))))
