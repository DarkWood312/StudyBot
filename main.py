import logging

import aiogram.utils.exceptions
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext, filters
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from emoji.core import emojize
from aiogram.utils.markdown import hbold, hcode, hlink

from gdz import GDZ
import db
from config import token, sql

logging.basicConfig(level=logging.DEBUG)
bot = Bot(token=token)
dp = Dispatcher(bot, storage=MemoryStorage())


class Marks(StatesGroup):
    is_continue = State()
    continue_ = State()


@dp.message_handler(filters.Text(startswith=['2', '3', '4', '5']), state='*')
async def average_mark(message: types.Message, state: FSMContext, amount_of_digits_after_comma=2,
                       is_undefined_symbols=True):
    text_of_marks = message.text.replace(' ', '')
    list_of_marks = []
    list_of_undefined_symbols = []
    for mark in text_of_marks:
        if mark in ['2', '3', '4', '5']:
            list_of_marks.append(int(mark))
        else:
            list_of_undefined_symbols.append(mark)

    await state.update_data(marks=list_of_marks)

    average = (sum(list_of_marks) / len(list_of_marks)).__round__(amount_of_digits_after_comma)
    better_mark_markup = types.InlineKeyboardMarkup()
    to_5 = types.InlineKeyboardButton('Хочу 5', callback_data='want_5')
    to_4 = types.InlineKeyboardButton('Хочу 4', callback_data='want_4')
    to_3 = types.InlineKeyboardButton('Хочу 3', callback_data='want_3')
    # cancel = types.InlineKeyboardButton('Отмена', callback_data='cancel')
    if average < 4.6:
        better_mark_markup.add(to_5)
    if average < 3.6:
        better_mark_markup.add(to_4)
    if average < 2.6:
        better_mark_markup.add(to_3)
    # if average < 4.6:
    #     better_mark_markup.add(cancel)

    await message.answer(f'Средний балл = <b>{str(average)}</b>', parse_mode=types.ParseMode.HTML,
                         reply_markup=better_mark_markup)
    if is_undefined_symbols:
        if len(list_of_undefined_symbols) > 0:
            await message.answer(
                f'Неизвестные символы, которые не учитывались: <code>{list_of_undefined_symbols}</code>',
                parse_mode=types.ParseMode.HTML)
    if average < 4.6:
        await Marks.continue_.set()


# @dp.message_handler(state=Marks.continue_)
# async def state_marks_continue_text(message: types.Message, state: FSMContext):
#     await state.finish()
#     await message.answer('Действие отменено')


@dp.callback_query_handler(state=Marks.continue_)
async def state_Marks_continue_(call: types.CallbackQuery, state: FSMContext):
    fives = 0
    fours = 0
    threes = 0
    if call.data == 'want_5':
        marks = await state.get_data()
        marks = marks['marks']
        while sum(marks + [5] * fives) / len(marks + [5] * fives) < 4.6:
            fives += 1
        avg_5 = (sum(marks + [5] * fives) / len(marks + [5] * fives)).__round__(2)
        await call.message.answer(f'Для *5* нужно:\n`{fives}` *пятерок* ({avg_5})', parse_mode=types.ParseMode.MARKDOWN)

    elif call.data == 'want_4':
        marks = await state.get_data()
        marks = marks['marks']
        while sum(marks + [5] * fives) / len(marks + [5] * fives) < 3.6:
            fives += 1
        avg_5 = (sum(marks + [5] * fives) / len(marks + [5] * fives)).__round__(2)
        while sum(marks + [4] * fours) / len(marks + [4] * fours) < 3.6:
            fours += 1
        avg_4 = (sum(marks + [4] * fours) / len(marks + [4] * fours)).__round__(2)
        await call.message.answer(
            f'Для *4* нужно:\n`{fives}` *пятерок* ({avg_5}) _или_\n`{fours}` *четверок* ({avg_4})',
            parse_mode=types.ParseMode.MARKDOWN)
    elif call.data == 'want_3':
        marks = await state.get_data()
        marks = marks['marks']
        while sum(marks + [5] * fives) / len(marks + [5] * fives) < 2.6:
            fives += 1
        avg_5 = (sum(marks + [5] * fives) / len(marks + [5] * fives)).__round__(2)
        while sum(marks + [4] * fours) / len(marks + [4] * fours) < 2.6:
            fours += 1
        avg_4 = (sum(marks + [4] * fours) / len(marks + [4] * fours)).__round__(2)
        while sum(marks + [3] * threes) / len(marks + [3] * threes) < 2.6:
            threes += 1
        avg_3 = (sum(marks + [3] * threes) / len(marks + [3] * threes)).__round__(2)
        await call.message.answer(
            f'Для *3* нужно:\n`{fives}` *пятерок* ({avg_5}) _или_\n`{fours}` *четверок* ({avg_4}) _или_\n`{threes}` *троек* ({avg_3})',
            parse_mode=types.ParseMode.MARKDOWN)
    elif call.data == 'cancel':
        await state.finish()
        await call.message.answer('Действие отменено')


@dp.message_handler(commands=['gs', 'ds'], state='*', user_id=db.owner_id)
async def OptionState(message: types.Message, state: FSMContext):
    state_ = await state.get_state()
    if state_ is not None:
        if message.text.lower() == '/gs':
            await message.answer(hcode(state_), parse_mode=types.ParseMode.HTML)
        elif message.text.lower() == '/ds':
            await state.finish()
            await message.answer(f'{hcode(state_)} удален', parse_mode=types.ParseMode.HTML)
    else:
        await message.answer('no state')


async def main_message(message: types.Message):
    await message.answer(db.gdz_help, parse_mode=types.ParseMode.MARKDOWN,
                         reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(
                             KeyboardButton(emojize(
                                 f'Сжатие - {":cross_mark:" if sql.get_data(message.from_user.id, "upscaled") == 1 else ":check_mark_button:"}'))))


@dp.message_handler(commands=['start'], state='*')
async def start_message(message: types.Message):
    sql.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name,
                 message.from_user.last_name)
    await main_message(message)


@dp.message_handler(commands=['author'], state='*')
async def author(message: types.Message):
    await message.answer(f'Папа: {hlink("Алекса", "https://t.me/DWiPok")}'
                         f'\nИсходный код: {hlink("Github", "https://github.com/DarkWood312/gdz_bot_for_10b")}',
                         parse_mode=types.ParseMode.HTML)


@dp.message_handler(commands=['docs', 'documents'], state='*')
async def documents(message: types.Message):
    inline_kb = types.InlineKeyboardMarkup()
    algm_button = types.InlineKeyboardButton('Мордкович Алгебра (2.6 MB)', callback_data='algm')
    inline_kb.row(algm_button)
    await message.answer('Документы', reply_markup=inline_kb)


@dp.message_handler(content_types=types.ContentType.TEXT, state='*')
async def other_messages(message: types.Message):
    sql.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name,
                 message.from_user.last_name)
    low = message.text.lower()
    gdz = GDZ(message.from_user.id)

    if 'сжатие' in low:
        sql.change_data_int(message.from_user.id, 'upscaled',
                            False if sql.get_data(message.from_user.id, 'upscaled') == True else True)
        await message.answer(
            f'Отправка фотографий с сжатием {"выключена" if sql.get_data(message.from_user.id, "upscaled") == True else "включена"}!',
            reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton(emojize(
                f'Сжатие - {":cross_mark:" if sql.get_data(message.from_user.id, "upscaled") == 1 else ":check_mark_button:"}'))))

    # elif low.startswith('2') | low.startswith('3') | low.startswith('4') | low.startswith('5'):
    #     await Marks.is_continue.set()
    #     await average_mark(message)

    # *  gdz...
    elif ('алгм' in low) or ('algm' in low):
        try:
            subject, paragaph, num = low.split(' ', 2)
            paragaph = int(paragaph)
            num = int(num)
            response = await gdz.algm_pomogalka(paragaph, num)
            for group in response:
                await message.answer_media_group(group)
        except ValueError:
            await message.answer('Некорректное число!')
        except:
            await message.answer('Не найдено заданием с таким номером!')

    elif ('алг' in low) or ('alg' in low):
        try:
            subject, var = low.split(' ', 1)
            var = int(var)
            response = await gdz.alg_euroki(var)
            for group in response:
                await message.answer_media_group(group)
        except ValueError:
            await message.answer('Некорректное число!')
        except:
            await message.answer('Не найдено заданием с таким номером!')

    elif ('гео' in low) or ('geo' in low):
        try:
            subject, var = low.split(' ', 1)
            var = int(var)
            response = await gdz.geom_megaresheba(var)
            for group in response:
                await message.answer_media_group(group)
        except ValueError:
            await message.answer('Некорректное число!')
        except:
            await message.answer('Не найдено заданием с таким номером!')

    elif ('анг' in low) or ('ang' in low):
        try:
            subject, page = low.split(' ', 1)
            page = int(page)
            response = await gdz.ang_megaresheba(page)
            for group in response:
                await message.answer_media_group(group)
        except ValueError:
            await message.answer('Некорректное число!')
        except ConnectionError:
            await message.answer('Не найдено страницы с таким номером!')
        except aiogram.utils.exceptions.URLHostIsEmpty:
            await message.answer(emojize('На сайте нет этого номера:sad_but_relieved_face:'))

    elif ('хим' in low) or ('him' in low):
        try:
            subject, tem, work, var = low.split(' ', 3)
            var = int(var)
            tem = int(tem)
            work = int(work)
            response = await gdz.him_putin(tem, work, var)
            for group in response:
                await message.answer_media_group(group)
        except ValueError:
            await message.answer('Некорректное число!')
        except:
            await message.answer('Не найдено заданием с таким номером!')

    elif ('кист' in low) or ('kist' in low):
        try:
            subject, page = low.split(' ', 1)
            page = int(page)
            response = await gdz.kist(page)
            await message.answer_photo(response)
        except ValueError:
            await message.answer('Некорректное число!')
        except:
            await message.answer('Не найдено заданием с таким номером!')


@dp.message_handler(content_types=types.ContentType.ANY, state='*')
async def other_content(message: types.Message):
    if message.from_user.id == db.owner_id:
        cp = message.content_type
        await message.answer(cp)
        if cp == 'sticker':
            await message.answer(hcode(message.sticker.file_id), parse_mode=types.ParseMode.HTML)
        elif cp == 'photo':
            await message.answer(hcode(message.photo[0].file_id), parse_mode=types.ParseMode.HTML)
        elif cp == 'audio':
            await message.answer(hcode(message.audio.file_id), parse_mode=types.ParseMode.HTML)
        elif cp == 'document':
            await message.answer(hcode(message.document.file_id), parse_mode=types.ParseMode.HTML)
        elif cp == 'video':
            await message.answer(hcode(message.video.file_id), parse_mode=types.ParseMode.HTML)
        elif cp == 'video_note':
            await message.answer(hcode(message.video_note.file_id), parse_mode=types.ParseMode.HTML)
        elif cp == 'voice':
            await message.answer(hcode(message.voice.file_id), parse_mode=types.ParseMode.HTML)
        else:
            await message.answer('undefined content_type')
    else:
        await message.answer('Я еще не настолько умный')


@dp.callback_query_handler(state='*')
async def callback(call: types.CallbackQuery):
    if call.data == 'algm':
        await call.message.answer_document(db.doc_ids['algm'])


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
