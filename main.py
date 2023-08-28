import logging

from aiogram.utils import exceptions
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext, filters
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, Message, \
    CallbackQuery, ParseMode
from emoji.core import emojize
from aiogram.utils.markdown import hbold, hcode, hlink
from netschoolapi.errors import AuthError

from keyboards import cancel_markup
from netschool import NetSchool

from defs import gdz_sender, cancel_state, main_message
from gdz import GDZ
import db
from config import token, sql

logging.basicConfig(level=logging.DEBUG)
bot = Bot(token=token)
dp = Dispatcher(bot, storage=MemoryStorage())


class Marks(StatesGroup):
    is_continue = State()
    continue_ = State()


class NetSchoolState(StatesGroup):
    login = State()
    password = State()

class SendMessage(StatesGroup):
    receiver = State()
    message = State()


class IsAdminFilter(filters.BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin):
        self.is_admin = is_admin

    async def check(self, message: Message):
        admins = await sql.get_admins()
        user = message.from_user.id
        return user in admins


dp.filters_factory.bind(IsAdminFilter)


@dp.message_handler(commands=['msg'], state='*', is_admin=True)
async def send_msg(message: Message):
    markup = InlineKeyboardMarkup()
    users = await sql.get_users()
    markup.row(InlineKeyboardButton('Отправить всем!', callback_data='all'))
    for user in users:
        markup.row(InlineKeyboardButton(text=f'{user[0]}, {user[2]}, {user[3]}, {user[4]}', callback_data=f'{user[0]}'))
    await message.answer('Выбор пользователя для отправки сообщения: ', reply_markup=markup)
    await SendMessage.receiver.set()


@dp.callback_query_handler(state=SendMessage.receiver)
async def state_SendMessage_receiver(call: CallbackQuery, state: FSMContext):
    if call.data == 'all':
        users_id = [user[0] for user in await sql.get_users()]
        await state.update_data(receivers=users_id)
    else:
        await state.update_data(receivers=[int(call.data)])
    await call.message.answer('Сообщение: ')
    await SendMessage.message.set()


@dp.message_handler(state=SendMessage.message, content_types=types.ContentType.ANY)
async def state_SendMessage_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    receivers = data['receivers']
    for receiver in receivers:
        username = await sql.get_data(receiver, 'username')
        user_name = await sql.get_data(receiver, 'user_name')
        try:
            await message.copy_to(receiver)
            if len(receivers) == 1:
                await message.answer(
                    f"""'<code>{message.text}</code>' успешно отправлено <a href="tg://user?id={receiver}">{username if username != 'None' else user_name}</a>""",
                    parse_mode=ParseMode.HTML)
        except exceptions.BotBlocked:
            await message.answer('Error. BotBlocked')
    await message.answer('Закончить монолог?', reply_markup=InlineKeyboardMarkup().row(
        InlineKeyboardButton('Закончить', callback_data='stop_monolog')))


@dp.callback_query_handler(state=SendMessage.message)
async def state_SendMessage_message_callback(call: CallbackQuery, state: FSMContext):
    if call.data == 'stop_monolog':
        await state.finish()
        await call.message.answer('Готово.')

@dp.message_handler(commands=['cancel'], state='*')
async def cancel(message: types.Message, state: FSMContext):
    await cancel_state(state)
    await message.answer('Действие отменено.')

@dp.message_handler(commands=['login'], state='*')
async def login(message: Message, state: FSMContext):
    await cancel_state(state)
    current_logpass = await sql.get_logpass(message.from_user.id)
    if not current_logpass is None:
        await message.answer(f'Действующий аккаунт: <tg-spoiler><b>{current_logpass["login"]}</b> - <b>{current_logpass["password"]}</b></tg-spoiler>', parse_mode=ParseMode.HTML)
    await message.answer('Введите логин от <a href="https://sgo.rso23.ru/">Сетевого города</a>: ', parse_mode=ParseMode.HTML, reply_markup=await cancel_markup())
    await NetSchoolState.login.set()


@dp.message_handler(state=NetSchoolState.login)
async def state_NetSchool_login(message: Message, state: FSMContext):
    log = message.text
    await state.update_data(log=log)
    await message.answer('Введите пароль: ')
    await NetSchoolState.password.set()


@dp.message_handler(state=NetSchoolState.password)
async def state_NetSchool_password(message: Message, state: FSMContext):
    pass_ = message.text
    log = (await state.get_data())['log']

    try:
        ns = await NetSchool(log, pass_)
        await ns.logout()
        await sql.change_data(message.from_user.id, 'netschool', f'{log}:::{pass_}')
        await message.answer('Успешно!')
        await cancel_state(state)
    except AuthError:
        await message.answer('Логин или пароль неверный!')
        await cancel_state(state)
        await login(message, state)



@dp.message_handler(commands=['mymarks'], state='*')
async def mark_report(message: Message, state: FSMContext):
    await cancel_state(state)
    logpass = await sql.get_logpass(message.from_user.id)
    if logpass is None:
        await message.answer('Войдите в <a href="https://sgo.rso23.ru/">Сетевой Город</a> командой /login !', parse_mode=ParseMode.HTML)
        return
    ns = await NetSchool(login=logpass['login'], password=logpass['password'])
    all_marks = await ns.get_marks()
    subjects = list(all_marks.keys())
    markup = InlineKeyboardMarkup()
    for subject in subjects:
        marks = all_marks[subject]
        string_marks = ''.join([str(m) for m in all_marks[subject]])
        avg = (sum(marks) / len(marks)).__round__(2)
        markup.add(InlineKeyboardButton(f'{subject} - {avg}', callback_data=string_marks))

    await message.answer('Оценки: ', reply_markup=markup)





@dp.message_handler(filters.Text(startswith=['2', '3', '4', '5']), state='*')
async def average_mark(message: Message, state: FSMContext, amount_of_digits_after_comma=2,
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
    if average < 4.6:
        better_mark_markup.add(to_5)
    if average < 3.6:
        better_mark_markup.add(to_4)
    if average < 2.6:
        better_mark_markup.add(to_3)

    await message.answer(f'Средний балл = <b>{str(average)}</b>', parse_mode=ParseMode.HTML,
                         reply_markup=better_mark_markup)
    if is_undefined_symbols:
        if len(list_of_undefined_symbols) > 0:
            await message.answer(
                f'Неизвестные символы, которые не учитывались: <code>{list_of_undefined_symbols}</code>',
                parse_mode=ParseMode.HTML)
    if average < 4.6:
        await Marks.continue_.set()


@dp.callback_query_handler(state=Marks.continue_)
async def state_Marks_continue_(call: CallbackQuery, state: FSMContext):
    fives = 0
    fours = 0
    threes = 0
    if call.data == 'want_5':
        marks = await state.get_data()
        marks = marks['marks']
        while sum(marks + [5] * fives) / len(marks + [5] * fives) < 4.6:
            fives += 1
        avg_5 = (sum(marks + [5] * fives) / len(marks + [5] * fives)).__round__(2)
        await call.message.answer(f'Для *5* нужно:\n`{fives}` *пятерок* ({avg_5})', parse_mode=ParseMode.MARKDOWN)

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
            parse_mode=ParseMode.MARKDOWN)
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
            parse_mode=ParseMode.MARKDOWN)
    elif call.data == 'cancel':
        await cancel_state(state)
        await call.message.answer('Действие отменено')
    else:
        await cancel_state(state)
        await callback(call, state)


@dp.message_handler(commands=['gs', 'ds'], state='*', is_admin=True)
async def OptionState(message: Message, state: FSMContext):
    state_ = await state.get_state()
    if state_ is not None:
        if message.text.lower() == '/gs':
            await message.answer(hcode(state_), parse_mode=ParseMode.HTML)
        elif message.text.lower() == '/ds':
            await state.finish()
            await message.answer(f'{hcode(state_)} удален', parse_mode=ParseMode.HTML)
    else:
        await message.answer('no state')


@dp.message_handler(commands=['start'], state='*')
async def start_message(message: Message, state: FSMContext):
    await cancel_state(state)
    await sql.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name,
                       message.from_user.last_name)
    await main_message(message)


@dp.message_handler(commands=['author'], state='*')
async def author(message: Message):
    await message.answer(f'Папа: {hlink("Александр", "https://t.me/DWiPok")}'
                         f'\nИсходный код: {hlink("Github", "https://github.com/DarkWood312/StudyBot")}',
                         parse_mode=ParseMode.HTML)


@dp.message_handler(commands=['docs', 'documents'], state='*')
async def documents(message: Message):
    inline_kb = types.InlineKeyboardMarkup()
    algm_button = types.InlineKeyboardButton('Мордкович Алгебра (2.6 MB)', callback_data='algm')
    inline_kb.row(algm_button)
    await message.answer('Документы', reply_markup=inline_kb)


@dp.message_handler(content_types=types.ContentType.TEXT, state='*')
async def other_messages(message: Message):
    await sql.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name,
                 message.from_user.last_name)
    low = message.text.lower()
    gdz = GDZ(message.from_user.id)

    if 'сжатие' in low:
        await sql.change_data_int(message.from_user.id, 'upscaled',
                            False if await sql.get_data(message.from_user.id, 'upscaled') == True else True)
        await message.answer(
            f'Отправка фотографий с сжатием {"выключена" if await sql.get_data(message.from_user.id, "upscaled") == True else "включена"}!',
            reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton(emojize(
                f'Сжатие - {":cross_mark:" if await sql.get_data(message.from_user.id, "upscaled") == 1 else ":check_mark_button:"}'))))

    # *  gdz...
    elif ('алгм' in low) or ('algm' in low):
        try:
            subject, paragaph, num = low.split(' ', 2)
            paragaph = int(paragaph)
            await gdz_sender(num, gdz.algm_pomogalka, message, 'Алгебра Мордкович', paragaph)
        except ValueError:
            await message.answer('Некорректное число!')
        except:
            await message.answer('Не найдено задания с таким номером!')

    elif ('алг' in low) or ('alg' in low):
        try:
            subject, var = low.split(' ', 1)
            await gdz_sender(var, gdz.alg_megaresheba, message, 'Алгебра')
        except ValueError:
            await message.answer('Некорректное число!')
        except:
            await message.answer('Не найдено задания с таким номером!')

    elif ('гео' in low) or ('geo' in low):
        try:
            subject, var = low.split(' ', 1)
            await gdz_sender(var, gdz.geom_megaresheba, message, 'Геометрия')
        except ValueError:
            await message.answer('Некорректное число!')
        except:
            await message.answer('Не найдено задания с таким номером!')

    elif ('физ' in low) or ('phiz' in low):
        try:
            subject, var = low.split(' ', 1)
            await gdz_sender(var, gdz.phiz_megaresheba, message, 'Физика')
        except ValueError:
            await message.answer('Некорректное число!')
        except:
            await message.answer('Не найдено задания с таким номером')

    elif ('анг' in low) or ('ang' in low):
        try:
            subject, page = low.split(' ', 1)
            await gdz_sender(page, gdz.ang_megaresheba, message, 'Английский')
        except ValueError:
            await message.answer('Некорректное число!')
        except ConnectionError:
            await message.answer('Не найдено страницы с таким номером!')
        except exceptions.URLHostIsEmpty:
            await message.answer(emojize('На сайте нет этого номера:sad_but_relieved_face:'))

    elif ('хим' in low) or ('him' in low):
        try:
            subject, tem, work, var = low.split(' ', 3)
            tem = int(tem)
            work = int(work)
            await gdz_sender(var, gdz.him_putin, message, 'Химия', tem, work)
        except ValueError:
            await message.answer('Некорректное число!')
        except:
            await message.answer('Не найдено заданием с таким номером!')

    elif ('инф' in low) or ('inf' in low):
        try:
            subject, task, num = low.split(' ', 2)
            await gdz_sender(num, gdz.inf_kpolyakova, message, 'Информатика Полякова', task)
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
async def other_content(message: Message):
    if message.from_user.id == db.owner_id:
        cp = message.content_type
        await message.answer(cp)
        if cp == 'sticker':
            await message.answer(hcode(message.sticker.file_id), parse_mode=ParseMode.HTML)
        elif cp == 'photo':
            await message.answer(hcode(message.photo[0].file_id), parse_mode=ParseMode.HTML)
        elif cp == 'audio':
            await message.answer(hcode(message.audio.file_id), parse_mode=ParseMode.HTML)
        elif cp == 'document':
            await message.answer(hcode(message.document.file_id), parse_mode=ParseMode.HTML)
        elif cp == 'video':
            await message.answer(hcode(message.video.file_id), parse_mode=ParseMode.HTML)
        elif cp == 'video_note':
            await message.answer(hcode(message.video_note.file_id), parse_mode=ParseMode.HTML)
        elif cp == 'voice':
            await message.answer(hcode(message.voice.file_id), parse_mode=ParseMode.HTML)
        else:
            await message.answer('undefined content_type')
    else:
        await message.answer('Я еще не настолько умный')


@dp.callback_query_handler(state='*')
async def callback(call: CallbackQuery, state: FSMContext):
    if call.data == 'cancel':
        await cancel_state(state)
        await call.message.answer('Действие отменено.')
    elif call.data == 'algm':
        await call.message.answer_document(db.doc_ids['algm'])
    elif call.data.startswith(tuple(['2', '3', '4', '5'])):
        call.message.text = call.data
        # await call.message.answer(call.message.text)
        await average_mark(message=call.message, state=state)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
