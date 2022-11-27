import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from emoji.core import emojize
from aiogram.utils.markdown import hbold, hcode, hlink

from gdz import GDZ
import db
from config import token, sql

logging.basicConfig(level=logging.DEBUG)
bot = Bot(token=token)
dp = Dispatcher(bot)


async def main_message(message: types.Message):
    await message.answer(db.gdz_help, parse_mode=types.ParseMode.MARKDOWN,
                         reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(
                             KeyboardButton(emojize(
                                 f'Сжатие - {":cross_mark:" if sql.get_data(message.from_user.id, "upscaled") == 1 else ":check_mark_button:"}'))))


async def average_mark(message: types.Message, amount_of_digits_after_comma=2, is_undefined_symbols=True):
    text_of_marks = message.text.replace(' ', '')
    list_of_marks = []
    list_of_undefined_symbols = []
    for mark in text_of_marks:
        if mark in ['2', '3', '4', '5']:
            list_of_marks.append(int(mark))
        else:
            list_of_undefined_symbols.append(mark)

    average = (sum(list_of_marks) / len(list_of_marks)).__round__(amount_of_digits_after_comma)

    await message.answer(f'Средний балл = <b>{str(average)}</b>', parse_mode=types.ParseMode.HTML)
    if is_undefined_symbols:
        if len(list_of_undefined_symbols) > 0:
            await message.answer(
                f'Неизвестные символы, которые не учитывались: <code>{list_of_undefined_symbols}</code>',
                parse_mode=types.ParseMode.HTML)


@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    sql.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name,
                 message.from_user.last_name)
    await main_message(message)


@dp.message_handler(commands=['author'])
async def author(message: types.Message):
    await message.answer(f'Папа: {hlink("Алекса", "https://t.me/DWiPok")}'
                         f'\nИсходный код: {hlink("Github", "https://github.com/DarkWood312/gdz_bot_for_10b")}',
                         parse_mode=types.ParseMode.HTML)


@dp.message_handler(content_types=types.ContentType.TEXT)
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

    elif low.startswith('2') | low.startswith('3') | low.startswith('4') | low.startswith('5'):
        await average_mark(message)

    # *  gdz...
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
            response = await gdz.ang_euroki(page)
            for text in response:
                await message.answer(text)
            await message.answer(f'https://www.euroki.org/gdz/ru/angliyskiy/10_klass/vaulina-spotlight-693/str-{page}')
        except ValueError:
            await message.answer('Некорректное число!')
        except ConnectionError:
            await message.answer('Не найдено страницы с таким номером!')

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
            


@dp.message_handler(content_types=types.ContentType.ANY)
async def other_content(message: types.Message):
    if message.from_user.id == db.owner_id:
        await message.answer(message.content_type)
        match message.content_type:
            case 'sticker':
                await message.answer(hcode(message.sticker.file_id), parse_mode=types.ParseMode.HTML)
            case 'photo':
                await message.answer(hcode(message.photo[0].file_id), parse_mode=types.ParseMode.HTML)
            case 'audio':
                await message.answer(hcode(message.audio.file_id), parse_mode=types.ParseMode.HTML)
            case 'document':
                await message.answer(hcode(message.document.file_id), parse_mode=types.ParseMode.HTML)
            case 'video':
                await message.answer(hcode(message.video.file_id), parse_mode=types.ParseMode.HTML)
            case 'video_note':
                await message.answer(hcode(message.video_note.file_id), parse_mode=types.ParseMode.HTML)
            case 'voice':
                await message.answer(hcode(message.voice.file_id), parse_mode=types.ParseMode.HTML)
            case _:
                await message.answer('undefined content_type')
    else:
        await message.answer('Я еще не настолько умный')



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
