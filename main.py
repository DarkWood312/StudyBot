import json
import logging
from random import shuffle

from aiogram.utils import exceptions
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext, filters
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, Message, \
    CallbackQuery, ParseMode, InputMediaPhoto
from emoji.core import emojize
from aiogram.utils.markdown import hbold, hcode, hlink
from netschoolapi.errors import AuthError

from keyboards import cancel_markup, reply_cancel_markup, menu_markup
from netschool import NetSchool

from defs import modern_gdz_sender, cancel_state, main_message
from gdz import GDZ
from modern_gdz import ModernGDZ
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


class Bind(StatesGroup):
    picked_source = State()
    picked_grade = State()
    picked_subject = State()
    picked_book = State()
    picked_alias = State()


class Orthoepy(StatesGroup):
    main = State()


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


# @dp.message_handler(commands=['login'], state='*')
# async def login(message: Message, state: FSMContext):
#     await cancel_state(state)
#     current_logpass = await sql.get_logpass(message.from_user.id)
#     if not current_logpass is None:
#         await message.answer(f'Действующий аккаунт: <tg-spoiler><b>{current_logpass["login"]}</b> - <b>{current_logpass["password"]}</b></tg-spoiler>', parse_mode=ParseMode.HTML)
#     await message.answer('Введите логин от <a href="https://sgo.rso23.ru/">Сетевого города</a>: ', parse_mode=ParseMode.HTML, reply_markup=await cancel_markup())
#     await NetSchoolState.login.set()
#
#
# @dp.message_handler(state=NetSchoolState.login)
# async def state_NetSchool_login(message: Message, state: FSMContext):
#     log = message.text
#     await state.update_data(log=log)
#     await message.answer('Введите пароль: ')
#     await NetSchoolState.password.set()
#
#
# @dp.message_handler(state=NetSchoolState.password)
# async def state_NetSchool_password(message: Message, state: FSMContext):
#     pass_ = message.text
#     log = (await state.get_data())['log']
#
#     try:
#         ns = await NetSchool(log, pass_)
#         await ns.logout()
#         await sql.change_data(message.from_user.id, 'netschool', f'{log}:::{pass_}')
#         await message.answer('Успешно!')
#         await cancel_state(state)
#     except AuthError:
#         await message.answer('Логин или пароль неверный!')
#         await cancel_state(state)
#         await login(message, state)

@dp.message_handler(state=Bind.picked_alias)
async def state_Bind_picked_alias(message: Message, state: FSMContext):
    await state.update_data({'alias': message.text.split(' ')[0].lower()})
    state_data = await state.get_data()
    alias = state_data['alias']

    old_data = await sql.get_data(message.from_user.id, 'aliases')
    old_data[alias] = state_data['book_url']  # ! TODO TypeError: 'NoneType' object does not support item assignment

    new_data = json.dumps(old_data)

    await sql.change_data_jsonb(message.from_user.id, 'aliases', new_data)

    for msg in state_data['msgs_to_delete']:
        await bot.delete_message(message.chat.id, msg)
    await message.answer(f'Alias: <b>{alias}</b> был успешно добавлен!', parse_mode=ParseMode.HTML)

    await cancel_state(state)


@dp.message_handler(state=Orthoepy.main)
async def state_Orthoepy_main(message: Message, state: FSMContext):
    if not message.text.isdigit() and 'Закончить' not in message.text:
        await message.answer('Ответ должен быть числом!')
        return
    data = await state.get_data()
    words = data['words']

    gl = ["у", "е", "ы", "а", "о", "э", "я", "и", "ю"]
    pos = data['pos']
    total = data['total']
    syllable = 0
    incorrect = data['incorrect']

    if pos + 1 == len(words) or 'Закончить' in message.text:
        correct = total - len(incorrect)
        await message.answer(f'total - {total}\ncorrect - {correct}\nincorrect - {len(incorrect)}', reply_markup=await menu_markup(message))
        await state.finish()
        return

    word = words[pos]
    wgl = []
    for letter in word:

        if letter.lower() in gl:
            wgl.append(letter.lower())
            if letter.isupper():
                syllable = len(wgl)

    if int(message.text) == syllable:
        await message.answer('Верно!')
        total += 1
    else:
        await message.answer(f'Неправильно! Правильный ответ - <b>{syllable}</b>', parse_mode=ParseMode.HTML,
                             reply_markup=await reply_cancel_markup())
        incorrect.append([word, message.text])
    pos += 1

    await message.answer(f'{pos + 1}/{len(words)}) {words[pos].lower()} --> ')
    await state.update_data({'words': words, 'pos': pos, 'total': total, 'incorrect': incorrect})
    await Orthoepy.main.set()


@dp.message_handler(commands=['mymarks'], state='*')
async def mark_report(message: Message, state: FSMContext):
    await cancel_state(state)
    logpass = await sql.get_logpass(message.from_user.id)
    if logpass is None:
        await message.answer('Войдите в <a href="https://sgo.rso23.ru/">Сетевой Город</a> командой /login !',
                             parse_mode=ParseMode.HTML)
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


@dp.message_handler(commands=['bind'], state='*')
async def bind(message: Message, state: FSMContext):
    await cancel_state(state)

    source_markup = InlineKeyboardMarkup()
    for gdz_source in db.available_gdzs.values():
        source_markup.row(InlineKeyboardButton(gdz_source, callback_data=gdz_source))
    source_markup.row(InlineKeyboardButton('Отмена', callback_data='cancel'))

    await message.answer('Выберите источник ГДЗ:', reply_markup=source_markup)

    await Bind.picked_source.set()


@dp.message_handler(commands='orthoepy', state='*')
async def orthoepy(message: Message, state: FSMContext):
    await cancel_state(state)

    with open('orthoepy.txt') as f:
        words = [w.strip() for w in f.readlines()]
        # shuffle(words)

    await message.answer(f'1/{len(words)}) {words[0].lower()} --> ', reply_markup=await reply_cancel_markup())

    await Orthoepy.main.set()
    await state.update_data({'words': words, 'pos': 0, 'total': 0, 'incorrect': []})


@dp.callback_query_handler(state=Bind.picked_source)
async def state_Bind_picked_source(call: CallbackQuery, state: FSMContext):
    if call.data == 'cancel':
        await cancel_state(state)
        await call.message.delete()

    await state.update_data({'source': call.data})

    grade_markup = InlineKeyboardMarkup()
    for grade in range(1, 12):
        grade = str(grade)
        grade_markup.add(InlineKeyboardButton(grade, callback_data=grade))
    grade_markup.row(InlineKeyboardButton('Отмена', callback_data='cancel'))

    await call.message.edit_text('Выберите класс: ')
    await call.message.edit_reply_markup(reply_markup=grade_markup)

    await Bind.picked_grade.set()


@dp.callback_query_handler(state=Bind.picked_grade)
async def state_Bind_picked_grade(call: CallbackQuery, state: FSMContext):
    if call.data == 'cancel':
        await cancel_state(state)
        await call.message.delete()

    await state.update_data({'grade': call.data})

    subjects_markup = InlineKeyboardMarkup()
    subjects = (await (ModernGDZ(call.from_user.id).GdzPutinaFun()).get_subjects())[f'klass-{call.data}'].keys()
    for subject in subjects:
        subjects_markup.add(InlineKeyboardButton(subject, callback_data=subject))
    subjects_markup.row(InlineKeyboardButton('Отмена', callback_data='cancel'))

    msg = await call.message.edit_text('Выберите предмет: ')
    await call.message.edit_reply_markup(reply_markup=subjects_markup)

    await state.update_data({'msgs_to_delete': [msg.message_id]})

    await Bind.picked_subject.set()


@dp.callback_query_handler(state=Bind.picked_subject)
async def state_Bind_picked_subject(call: CallbackQuery, state: FSMContext):
    if call.data == 'cancel':
        await cancel_state(state)
        await call.message.delete()
    state_data = await state.get_data()
    await state.update_data({'subject': call.data})

    mgdz = ModernGDZ(call.from_user.id)
    sgdz = None
    if state_data['source'] == db.available_gdzs['gdz_putina']:
        sgdz = mgdz.GdzPutinaFun()
    subject_url = await sgdz.get_subject_url(state_data['grade'], call.data)
    books_data = await sgdz.get_books(subject_url)
    await state.update_data({'books_data': books_data})

    msgs_to_delete = state_data['msgs_to_delete']
    await call.message.delete()

    for i in range(0, len(books_data)):
        try:
            bmarkup = InlineKeyboardMarkup().add(InlineKeyboardButton('Выбрать', callback_data=str(i)))
            msg = await call.message.answer_photo(books_data[i]["img_url"],
                                                  caption=f'<b>{i + 1} / {len(books_data)}</b>. <a href="{books_data[i]["book_url"]}">{books_data[i]["img_title"]}</a>\n<code>{books_data[i]["author"]}</code>',
                                                  parse_mode=ParseMode.HTML, reply_markup=bmarkup,
                                                  disable_notification=True)
            msgs_to_delete.append(msg.message_id)
        except:
            print(books_data[i])
    await state.update_data({'msgs_to_delete': msgs_to_delete})
    await Bind.picked_book.set()


@dp.callback_query_handler(state=Bind.picked_book)
async def state_Bind_picked_book(call: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    await state.update_data({'book_url': state_data['books_data'][int(call.data)]['book_url']})

    msg = await call.message.answer(
        'Введите alias для этого предмета:\nНапример: <code>алг</code> (пример поиска номера: <i>алг 135</i>). <i>алг</i> - это '
        'alias для вашего предмета, <i>135</i> это номер задания и тп. ',
        parse_mode=ParseMode.HTML, reply_markup=await cancel_markup())

    msgs_to_delete = state_data['msgs_to_delete']
    msgs_to_delete.append(msg.message_id)
    await state.update_data({'msgs_to_delete': msgs_to_delete})

    await Bind.picked_alias.set()


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
        await sql.change_data_type(message.from_user.id, 'upscaled',
                                   False if await sql.get_data(message.from_user.id, 'upscaled') == True else True)
        await message.answer(
            f'Отправка фотографий с сжатием {"выключена" if await sql.get_data(message.from_user.id, "upscaled") == True else "включена"}!',
            reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton(emojize(
                f'Сжатие - {":cross_mark:" if await sql.get_data(message.from_user.id, "upscaled") == 1 else ":check_mark_button:"}'))))

    else:
        await message.answer('<i>ГДЗ в разработке...</i>', parse_mode=ParseMode.HTML)  # ! TODO GDZ
        # mgdz = ModernGDZ(message.from_user.id)
        # aliases = await sql.get_data(message.from_user.id, 'aliases')
        # if low in aliases:
        #

    # *  gdz...
    # elif ('алгм' in low) or ('algm' in low):
    #     try:
    #         subject, paragaph, num = low.split(' ', 2)
    #         paragaph = int(paragaph)
    #         await gdz_sender(num, gdz.algm_pomogalka, message, 'Алгебра Мордкович', paragaph)
    #     except ValueError:
    #         await message.answer('Некорректное число!')
    #     except:
    #         await message.answer('Не найдено задания с таким номером!')
    #
    # elif ('алг' in low) or ('alg' in low):
    #     try:
    #         subject, var = low.split(' ', 1)
    #         await gdz_sender(var, gdz.alg_megaresheba, message, 'Алгебра')
    #     except ValueError:
    #         await message.answer('Некорректное число!')
    #     except:
    #         await message.answer('Не найдено задания с таким номером!')
    #
    # elif ('гео' in low) or ('geo' in low):
    #     try:
    #         subject, var = low.split(' ', 1)
    #         await gdz_sender(var, gdz.geom_megaresheba, message, 'Геометрия')
    #     except ValueError:
    #         await message.answer('Некорректное число!')
    #     except:
    #         await message.answer('Не найдено задания с таким номером!')
    #
    # elif ('физ' in low) or ('phiz' in low):
    #     try:
    #         subject, var = low.split(' ', 1)
    #         await gdz_sender(var, gdz.phiz_megaresheba, message, 'Физика')
    #     except ValueError:
    #         await message.answer('Некорректное число!')
    #     except:
    #         await message.answer('Не найдено задания с таким номером')
    #
    # elif ('анг' in low) or ('ang' in low):
    #     try:
    #         subject, page = low.split(' ', 1)
    #         await gdz_sender(page, gdz.ang_megaresheba, message, 'Английский')
    #     except ValueError:
    #         await message.answer('Некорректное число!')
    #     except ConnectionError:
    #         await message.answer('Не найдено страницы с таким номером!')
    #     except exceptions.URLHostIsEmpty:
    #         await message.answer(emojize('На сайте нет этого номера:sad_but_relieved_face:'))
    #
    # elif ('хим' in low) or ('him' in low):
    #     try:
    #         subject, tem, work, var = low.split(' ', 3)
    #         tem = int(tem)
    #         work = int(work)
    #         await gdz_sender(var, gdz.him_putin, message, 'Химия', tem, work)
    #     except ValueError:
    #         await message.answer('Некорректное число!')
    #     except:
    #         await message.answer('Не найдено заданием с таким номером!')
    #
    # elif ('инф' in low) or ('inf' in low):
    #     try:
    #         subject, task, num = low.split(' ', 2)
    #         await gdz_sender(num, gdz.inf_kpolyakova, message, 'Информатика Полякова', task)
    #     except ValueError:
    #         await message.answer('Некорректное число!')
    #     except:
    #         await message.answer('Не найдено заданием с таким номером!')
    #
    #
    # elif ('кист' in low) or ('kist' in low):
    #     try:
    #         subject, page = low.split(' ', 1)
    #         page = int(page)
    #         response = await gdz.kist(page)
    #         await message.answer_photo(response)
    #     except ValueError:
    #         await message.answer('Некорректное число!')
    #     except:
    #         await message.answer('Не найдено заданием с таким номером!')


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
