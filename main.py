import asyncio
import logging
import random
import sys
from random import shuffle

import nltk
from aiogram.enums import ParseMode
from aiogram import Bot, Dispatcher, types, F, Router, html
from aiogram.filters import Filter, Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, Message, \
    CallbackQuery, InputMediaPhoto, InputMediaDocument, InputFile, FSInputFile, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold, hcode, hlink, hide_link
from aiogram.utils.media_group import MediaGroupBuilder

from exceptions import NumDontExistError, BaseDontExistError
from keyboards import cancel_markup, reply_cancel_markup, menu_markup, orthoepy_word_markup
# from netschool import NetSchool


from defs import cancel_state, main_message, orthoepy_word_formatting, command_alias, text_analysis, num_base_converter
from gdz import GDZ
from modern_gdz import ModernGDZ
import db
from config import token, sql

router = Router()
dp = Dispatcher(storage=MemoryStorage())


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


class Test(StatesGroup):
    credentials = State()


class Aliases(StatesGroup):
    main = State()


class WordCloud(StatesGroup):
    settings_input = State()


class BaseConverter(StatesGroup):
    num = State()
    base = State()


class IsAdmin(Filter):
    def __init__(self, is_admin: bool = True) -> None:
        self.is_admin = is_admin

    async def __call__(self, message: Message) -> bool:
        admins = await sql.get_admins()
        user_id = message.from_user.id
        return int(user_id) in admins


@dp.message(IsAdmin(True), Command('msg'))
async def send_msg(message: Message, state: FSMContext):
    markup = InlineKeyboardBuilder()
    users = await sql.get_users()
    markup.row(InlineKeyboardButton(text='Отправить всем!', callback_data='all'))
    for user in users:
        markup.row(InlineKeyboardButton(text=f'{user[0]}, {user[2]}, {user[3]}, {user[4]}', callback_data=f'{user[0]}'))
    await message.answer('Выбор пользователя для отправки сообщения: ', reply_markup=markup.as_markup())
    await state.set_state(SendMessage.receiver)


@dp.callback_query(SendMessage.receiver)
async def state_SendMessage_receiver(call: CallbackQuery, state: FSMContext):
    if call.data == 'all':
        users_id = [user[0] for user in await sql.get_users()]
        await state.update_data(receivers=users_id)
    else:
        await state.update_data(receivers=[int(call.data)])
    await call.message.answer('Сообщение: ')
    await state.set_state(SendMessage.message)
    await call.answer()


@dp.message(SendMessage.message)
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
        except Exception as e:
            await message.answer('Error. BotBlocked')
            await message.answer(e)
    await message.answer('Закончить монолог?', reply_markup=InlineKeyboardBuilder().row(
        InlineKeyboardButton(text='Закончить', callback_data='stop_monolog')).as_markup())


@dp.callback_query(SendMessage.message)
async def state_SendMessage_message_callback(call: CallbackQuery, state: FSMContext):
    if call.data == 'stop_monolog':
        await cancel_state(state)
        await call.message.answer('Готово.')
        await call.answer()


@dp.message(Command('cancel'))
async def cancel(message: types.Message, state: FSMContext):
    await cancel_state(state)
    msg = await message.answer('Действие отменено.')
    await message.delete()

    await asyncio.sleep(2)
    await msg.delete()


@dp.message(CommandStart())
async def start_message(message: Message, state: FSMContext):
    await cancel_state(state)
    await sql.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name,
                       message.from_user.last_name)
    await sql.add_wordcloud_user(user_id=message.from_user.id)
    await main_message(message)
    await message.delete()


# @dp.message(Command('login'))
# async def login(message: Message, state: FSMContext):
#     await cancel_state(state)
#     current_logpass = await sql.get_logpass(message.from_user.id)
#     if not current_logpass is None:
#         await message.answer(f'Действующий аккаунт: <tg-spoiler><b>{current_logpass["login"]}</b> - <b>{current_logpass["password"]}</b></tg-spoiler>', parse_mode=ParseMode.HTML)
#     await message.answer('Введите логин от <a href="https://sgo.rso23.ru/">Сетевого города</a>: ', parse_mode=ParseMode.HTML, reply_markup=await cancel_markup())
#     await state.set_state(NetSchoolState.login)
#
#
# @dp.message(NetSchoolState.login)
# async def state_NetSchool_login(message: Message, state: FSMContext):
#     log = message.text
#     await state.update_data(log=log)
#     await message.answer('Введите пароль: ')
#     await state.set_state(NetSchoolState.password)
#
#
# @dp.message(NetSchoolState.password)
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

@dp.message(Bind.picked_alias)
async def state_Bind_picked_alias(message: Message, state: FSMContext, bot: Bot):
    await state.update_data({'alias': message.text.split(' ')[0].lower()})
    state_data = await state.get_data()
    alias = state_data['alias']

    old_data = await sql.get_data(message.from_user.id, 'aliases')
    old_data[alias] = state_data['book_url']

    await sql.change_data_jsonb(message.from_user.id, 'aliases', old_data)
    msg_ = await message.answer(f'Alias: <b>{alias}</b> был успешно добавлен!', parse_mode=ParseMode.HTML)

    await cancel_state(state)
    for msg in state_data['msgs_to_delete']:
        await bot.delete_message(message.chat.id, msg)

    await asyncio.sleep(3)
    await msg_.delete()
    await message.delete()


@dp.message(Orthoepy.main)
async def state_Orthoepy_main(message: Message, state: FSMContext, bot: Bot, call: CallbackQuery = None):
    data = await state.get_data()
    msgs_to_delete = data['msgs_to_delete']
    total = data['total']
    words = data['words']
    incorrect = data['incorrect']
    correct = data['correct']
    test_mode = data['test_mode'] if 'test_mode' in data else False
    user_credentials = data['user_credentials'] if test_mode else None
    test_settings = data['test_settings'] if test_mode is not False else None

    if 'Закончить' in message.text or call is not None:
        # correct = total - len(incorrect)
        percentage = round(len(correct) / total * 100 if total > 0 else 0, 1)
        text = f'<b>Статистика по орфоэпии:</b>\n<i>Всего</i> - <code>{total}</code>\n<i>Правильных</i> - <code>{len(correct)}</code>\n<i>Неправильных</i> - <code>{len(incorrect)}</code>\n<i>В процентах</i> - <code>{percentage}%</code>'
        wl_correct = [f'<b>{w}</b> - ✅' for w in correct]
        wl_incorrect = [f'<b>{w[0]}</b> - ❌ (Ответил: <code>{w[1]}</code>)' for w in incorrect]
        text = f'{text}\n\n' + '\n'.join(wl_incorrect) + ('\n' if len(incorrect) > 0 else '') + '\n'.join(wl_correct)
        if test_mode:
            text_teacher = f'Результат <a href="tg://user?id={user_credentials[1]}">{user_credentials[0]}</a>:\n{text}'
        if call is not None:
            message = call.message
            user_id = call.from_user.id
        else:
            user_id = message.from_user.id
            await message.delete()

        await message.answer(text, reply_markup=await menu_markup(user_id), parse_mode=ParseMode.HTML)
        if not test_mode:
            for m in msgs_to_delete:
                await bot.delete_message(message.chat.id, m)
        await cancel_state(state)

        if test_mode:
            await bot.send_message(test_settings['receiver'], text_teacher, parse_mode=ParseMode.HTML)
            await message.answer('Работа отправлена учителю!🥳')

        if len(incorrect) > 0:
            for incorrect_word in incorrect:
                await sql.add_orthoepy(incorrect_word[0], 1)

        # * Randoms
        rand = random.randint(1, 100)
        total_floor = 10
        if rand <= 1.25 and total > 0:
            await message.answer_video_note(db.video_note_answers['nikita_lucky-1'])
        elif 1.25 < rand <= 2.5 and total > 0:
            await message.answer_video_note(db.video_note_answers['nikita_lucky-2'])
        elif 2.5 < rand <= 3.75 and total > 0:
            await message.answer_video_note(db.video_note_answers['nikita_lucky-3'])
        elif 3.75 < rand <= 5 and total > 0:
            await message.answer_video_note(db.video_note_answers['nikita_lucky-4'])
        elif percentage == 100 and total == 1:
            await message.answer_video_note(db.video_note_answers['nikita_fake_100-1'])
        elif percentage == 0 and total == 1:
            await message.answer_video_note(db.video_note_answers['nikita_fake_100-2'])
        elif percentage == 0 and total >= total_floor:
            if rand <= 25:
                await message.answer_video_note(db.video_note_answers['nikita_fu-2'])
                await message.answer_video_note(db.video_note_answers['nikita_fu-3'])
            else:
                await message.answer_video_note(db.video_note_answers['nikita_fu-1'])
        elif percentage <= 10 and total >= total_floor:
            if rand <= 10:
                await message.answer_video_note(db.video_note_answers['nikita_less10-2'])
            else:
                await message.answer_video_note(db.video_note_answers['nikita_less10-1'])
        elif 80 > percentage >= 50 and total >= total_floor:
            await message.answer_video_note(db.video_note_answers['nikita_mid-1'])
        elif 90 > percentage >= 80 and total >= total_floor:
            await message.answer_video_note(db.video_note_answers['nikita_high-1'])
        elif 100 > percentage >= 90 and total >= total_floor:
            await message.answer_video_note(db.video_note_answers['nikita_high-2'])
        elif percentage == 100 and total >= len(words):
            await message.answer_video_note(db.video_note_answers['holid_100-1'])


@dp.callback_query(Orthoepy.main)
async def callback_state_Orthoepy_main(call: CallbackQuery, state: FSMContext, bot: Bot):
    if call.data == '_NO-DATA':
        await call.answer()
        return
    data = await state.get_data()
    msgs_to_delete = data['msgs_to_delete']
    words = data['words']
    pos = data['pos']
    total = data['total']
    incorrect = data['incorrect']
    correct = data['correct']
    test_mode = data['test_mode'] if 'test_mode' in data else False

    amount_of_words = len(words)
    if test_mode:
        test_settings = data['test_settings']
        amount_of_words = test_settings['amount_of_words']
    syllable = 0

    word = words[pos]
    wgl = []
    for letter in word:

        if letter.lower() in db.gl:
            wgl.append(letter.lower())
            if letter.isupper():
                syllable = len(wgl)
    edit_markup = InlineKeyboardBuilder()
    if int(call.data) == syllable:
        if not test_mode:
            button = InlineKeyboardButton(text=f'{word} ✅', callback_data='_NO-DATA')
            edit_markup.add(button)
        correct.append(word)
    else:
        if not test_mode:
            button = InlineKeyboardButton(text=f'{word} ❌', callback_data='_NO-DATA')
            edit_markup.add(button)
        incorrect.append([word, call.data])
    if test_mode:
        edit_markup.add(InlineKeyboardButton(text=f'{call.data}🚦', callback_data='_NO-DATA'))
    await call.message.edit_reply_markup(reply_markup=edit_markup.as_markup())
    total += 1
    pos += 1

    await state.update_data(
        {'words': words, 'pos': pos, 'total': total, 'correct': correct, 'incorrect': incorrect,
         'msgs_to_delete': msgs_to_delete})
    await call.answer()
    if pos == amount_of_words:
        await state_Orthoepy_main(call.message, state, bot, call)
        return

    gls = [letter.lower() for letter in words[pos] if letter.lower() in db.gl]
    gls_markup = await orthoepy_word_markup(gls)
    msg = await call.message.answer(await orthoepy_word_formatting(words, pos, amount_of_words),
                                    parse_mode=ParseMode.HTML,
                                    reply_markup=gls_markup)
    if 'show_answers' in data:
        if data['show_answers']:
            await call.message.answer(words[pos])
    msgs_to_delete.append(msg.message_id)
    await call.answer()


@dp.message(Test.credentials)
async def state_Test_credentials(message: Message, state: FSMContext):
    with open('test_settings.txt') as f:
        settings = {}
        for line in f.readlines():
            line = line.strip()
            p = line.split('=')
            settings[p[0]] = int(p[1]) if p[1].isdigit() else p[1]
    await state.update_data(
        {'user_credentials': [message.text, message.from_user.id], 'test_mode': True, 'test_settings': settings})
    await orthoepy(message, state, test_mode=settings)


# @dp.message(Command('mymarks'))
# async def mark_report(message: Message, state: FSMContext):
#     await cancel_state(state)
#     logpass = await sql.get_logpass(message.from_user.id)
#     if logpass is None:
#         await message.answer('Войдите в <a href="https://sgo.rso23.ru/">Сетевой Город</a> командой /login !',
#                              parse_mode=ParseMode.HTML)
#         return
#     ns = await NetSchool(login=logpass['login'], password=logpass['password'])
#     all_marks = await ns.get_marks()
#     subjects = list(all_marks.keys())
#     markup = InlineKeyboardBuilder()
#     for subject in subjects:
#         marks = all_marks[subject]
#         string_marks = ''.join([str(m) for m in all_marks[subject]])
#         avg = round((sum(marks) / len(marks)), 2)
#         markup.add(InlineKeyboardButton(text=f'{subject} - {avg}', callback_data=string_marks))
#
#     await message.answer('Оценки: ', reply_markup=markup.as_markup())
#
#     await message.delete()

@dp.message(Command('base_converter'))
async def base_converter(message: Message, state: FSMContext):
    await cancel_state(state)
    await state.set_state(BaseConverter.num)
    guide1_msg = await message.answer('Напишите значение и основание:\n', reply_markup=await reply_cancel_markup())
    guide_text = f'<b>Формат:</b> {html.quote("<значение> <к основанию> (тогда основание СС <значение> считается 10) ИЛИ <значение> <из основания> <к основанию>")} \n<b>Пример</b>: <code>60 2</code> ==> <i>60\u2081\u2080 --> 111100\u2082</i>\n<code>111100 2 10</code> ==> <i>111100\u2082 --> 60\u2081\u2080</i>'
    guide_msg = await message.answer(guide_text, parse_mode=ParseMode.HTML)
    await state.update_data({'guide_text': guide_text, 'msgs_to_delete': [guide1_msg, guide_msg]})
    await message.delete()


@dp.message(BaseConverter.num)
async def BaseConverter_num(message: Message, state: FSMContext, bot: Bot):
    await message.delete()
    data = await state.get_data()
    if 'закончить' in message.text.lower():
        for msg in data['msgs_to_delete']:
            await bot.delete_message(message.from_user.id, msg.message_id)
        await message.answer('Готово!', reply_markup=await menu_markup(message.from_user.id))
        await cancel_state(state)
        return
    args = message.text.split(' ')
    num = args[0]
    if len(args) == 2:
        to_base = args[1]
        from_base = 10
    elif len(args) == 3:
        to_base = args[2]
        from_base = args[1]
    else:
        guide_text = await message.answer(data['guide_text'])
        msgs_to_delete = data['msgs_to_delete']
        msgs_to_delete.append(guide_text)
        await state.update_data({'msgs_to_delete': msgs_to_delete})
        return
    try:
        conv = await num_base_converter(num, int(to_base), int(from_base))
    except NumDontExistError as e:
        await message.answer(f"<b>Ошибка</b>: Значениe '<code>{e.args[1]}</code>' не существуют в СС с основанием '<code>{e.args[2]}</code>'", parse_mode=ParseMode.HTML)
        return
    except BaseDontExistError:
        await message.answer('<b>Ошибка</b>: СС с основанием > <code>36</code>', parse_mode=ParseMode.HTML)
        return
    text = bytes(fr'{hcode(num)}\u208' + fr'\u208'.join([*str(from_base)]) + fr' --> {hcode(conv)}\u208' + r'\u208'.join([*str(to_base)]), 'utf-8').decode('unicode_escape')
    await message.answer(text, parse_mode=ParseMode.HTML)


# @dp.message(BaseConverter.num)
# async def BaseConverter_num(message: Message, state: FSMContext):
#     markup = InlineKeyboardBuilder()
#     markup.add(InlineKeyboardButton(text='ИЗ основания 10', callback_data='from_base'))
#     markup.add(InlineKeyboardButton(text='В основание 2', callback_data='to_base'))
#
#     conv = await num_base_converter(message.text.lower(), 2)
#     main_msg = await message.answer(hcode(message.text) + u'\u2081\u2080 --> ' + hcode(str(conv)) + u'\u2082',
#                                     reply_markup=markup.as_markup())
#     await state.update_data(
#         {'num': message.text.lower(), 'markup': markup, 'from_base': 10, 'to_base': 2, 'main_msg': main_msg})
#
#     await message.delete()
#
#
# @dp.callback_query(BaseConverter.num)
# async def BaseConverter_num_callback(call: CallbackQuery, state: FSMContext):
#     to_del = await call.message.answer('Введите основание СС')
#     await state.update_data({'type': call.data, 'msg_to_del': to_del})
#     await state.set_state(BaseConverter.base)
#
#     await call.answer()
#
#
# @dp.message(BaseConverter.base)
# async def BaseConverter_base(message: Message, state: FSMContext, bot: Bot):
#     data = await state.get_data()
#     if not message.text.isdigit():
#         await message.answer('Основание СС должно быть записано числом!')
#     await state.update_data({data['type']: int(message.text)})
#     conv = await num_base_converter(data['num'], data['to_base'], data['from_base'])
#     text = bytes(
#         fr'{data["num"]}\u208' + fr'\u208'.join([*str(data['from_base'])]) + fr' --> {conv}\u208' + r'\u208'.join(
#             [*str(data['to_base'])]), 'utf-8').decode('unicode_escape')
#
#     markup = InlineKeyboardBuilder()
#     markup.add(InlineKeyboardButton(text=f'ИЗ основания {data["from_base"]}', callback_data='from_base'))
#     markup.add(InlineKeyboardButton(text=f'В основание {data["to_base"]}', callback_data='to_base'))
#
#     # await data['main_msg'].edit_text(str(text), parse_mode=ParseMode.HTML)
#     await bot.edit_message_text(data['main_msg'].message_id, text)
#     # await data['main_msg'].edit_reply_markup(markup.as_markup())
#
#     await state.set_state(BaseConverter.num)
#
#     await message.delete()
#     # await data['to_del'].delete()


@dp.message(F.text.startswith(('2', '3', '4', '5')))
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

    average = round(sum(list_of_marks) / len(list_of_marks), amount_of_digits_after_comma)
    better_mark_markup = InlineKeyboardBuilder()
    to_5 = types.InlineKeyboardButton(text='Хочу 5', callback_data='want_5')
    to_4 = types.InlineKeyboardButton(text='Хочу 4', callback_data='want_4')
    to_3 = types.InlineKeyboardButton(text='Хочу 3', callback_data='want_3')
    if average < 4.6:
        better_mark_markup.add(to_5)
    if average < 3.6:
        better_mark_markup.add(to_4)
    if average < 2.6:
        better_mark_markup.add(to_3)

    await message.answer(f'Средний балл = <b>{str(average)}</b>', parse_mode=ParseMode.HTML,
                         reply_markup=better_mark_markup.as_markup())
    if is_undefined_symbols:
        if len(list_of_undefined_symbols) > 0:
            await message.answer(
                f'Неизвестные символы, которые не учитывались: <code>{list_of_undefined_symbols}</code>',
                parse_mode=ParseMode.HTML)
    if average < 4.6:
        await state.set_state(Marks.continue_)


@dp.callback_query(Marks.continue_)
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
    await call.answer()


@dp.message(IsAdmin(), Command('gs', 'ds'))
async def OptionState(message: Message, state: FSMContext):
    state_ = await state.get_state()
    if state_ is not None:
        if message.text.lower() == '/gs':
            await message.answer(hcode(state_), parse_mode=ParseMode.HTML)
        elif message.text.lower() == '/ds':
            await state.clear()
            await message.answer(f'{hcode(state_)} удален', parse_mode=ParseMode.HTML)
    else:
        await message.answer('no state')


@dp.message(Command('bind'))
async def bind(message: Message, state: FSMContext):
    await cancel_state(state)

    source_markup = InlineKeyboardBuilder()
    for gdz_source in db.available_gdzs.values():
        source_markup.row(InlineKeyboardButton(text=gdz_source, callback_data=gdz_source))
    source_markup.row(InlineKeyboardButton(text='Отмена', callback_data='cancel'))

    await message.answer('Выберите источник ГДЗ:', reply_markup=source_markup.as_markup())

    await message.delete()

    await state.set_state(Bind.picked_source)


@dp.message(IsAdmin(), Command('test_settings'))
async def orthoepy_test_settings(message: Message):
    params = message.text.split(' ')
    if len(params) < 2:
        await message.answer('Неправильное количество параметров!')
        return
    if params[1] == 'get':
        with open('test_settings.txt') as f:
            await message.answer('\n'.strip().join(f.readlines()))
        return
    if len(params) != 3:
        await message.answer('Неправильное количество параметров!')
        return

    receiver = int(params[1])
    amount_of_words = int(params[2])
    with open('test_settings.txt', 'w') as f:
        f.write(f'''receiver={receiver}\namount_of_words={amount_of_words}'''.strip())
    await message.answer('Done!')


@dp.message(Command('test'))
async def orthoepy_test(message: Message, state: FSMContext):
    await cancel_state(state)
    params = message.text.split(' ')

    await message.answer('<b>Введите свои данные</b> (<i>например:</i> <code>Иванов А, 11Б</code>): ',
                         parse_mode=ParseMode.HTML)
    await state.set_state(Test.credentials)
    if len(params) == 2:
        if params[1] == 'ans!':
            await state.update_data({'show_answers': True})


@dp.message(Command('orthoepy'))
async def orthoepy(message: Message, state: FSMContext, test_mode: bool | dict = False):
    if test_mode is False:
        await cancel_state(state)

    with open('orthoepy.txt', encoding='utf-8') as f:
        words = [w.strip() for w in f.readlines()]
        shuffle(words)
    amount_of_words = len(words)
    if test_mode is not False:
        amount_of_words = test_mode['amount_of_words']

    gls = [letter.lower() for letter in words[0] if letter.lower() in db.gl]

    rules = await message.answer('<b>Выберите гласную на которую падает ударение.</b>',
                                 reply_markup=await reply_cancel_markup(), parse_mode=ParseMode.HTML)
    msg = await message.answer(await orthoepy_word_formatting(words, 0, amount_of_words),
                               reply_markup=await orthoepy_word_markup(gls),
                               parse_mode=ParseMode.HTML)

    await message.delete()

    await state.set_state(Orthoepy.main)
    data = await state.get_data()
    if 'show_answers' in data:
        if data['show_answers']:
            await message.answer(words[0])
    await state.update_data(
        {'words': words, 'pos': 0, 'total': 0, 'correct': [], 'incorrect': [],
         'msgs_to_delete': [msg.message_id, rules.message_id],
         'gls': gls})
    if test_mode is not False:
        await state.update_data({'test_mode': True})


@dp.message(Command('ostats'))
async def orthoepy_statistics(message: Message, state: FSMContext):
    await cancel_state(state)
    maximum = message.text.split(' ')[1] if len(message.text.split(' ')) > 1 else 10
    if not str(maximum).isdigit():
        await message.answer('<b>Использование:</b> /ostats <кол-во строк>', parse_mode=ParseMode.HTML)
        return
    else:
        maximum = int(maximum)
        statistics = (await sql.get_orthoepy(maximum)).items()
        text = f'Топ <b>{maximum}</b> слов, которые вызывают проблемы в орфоэпии:\n' + '\n'.join(
            [f'<b>{l[0]}</b>: <code>{l[1]}</code>' for l in statistics])
        await message.answer(text, parse_mode=ParseMode.HTML)
    await message.delete()


@dp.callback_query(Bind.picked_source)
async def state_Bind_picked_source(call: CallbackQuery, state: FSMContext):
    if call.data == 'cancel':
        await cancel_state(state)
        await call.message.delete()
        await call.answer()
        return

    await state.update_data({'source': call.data})

    grade_markup = InlineKeyboardBuilder()
    for grade in range(1, 12):
        grade = str(grade)
        grade_markup.add(InlineKeyboardButton(text=grade, callback_data=grade))
    # grade_markup.row(InlineKeyboardButton(text='Отмена', callback_data='cancel'))

    await call.message.edit_text('Выберите класс: ')
    await call.message.edit_reply_markup(reply_markup=grade_markup.as_markup())

    await state.set_state(Bind.picked_grade)
    await call.answer()


@dp.callback_query(Bind.picked_grade)
async def state_Bind_picked_grade(call: CallbackQuery, state: FSMContext):
    if call.data == 'cancel':
        await cancel_state(state)
        await call.message.delete()
        await call.answer()
        return

    await state.update_data({'grade': call.data})

    subjects_markup = InlineKeyboardBuilder()
    subjects = (await (ModernGDZ(call.from_user.id).GdzPutinaFun()).get_subjects())[f'klass-{call.data}'].keys()
    for subject in subjects:
        subjects_markup.add(InlineKeyboardButton(text=subject, callback_data=subject))
    subjects_markup.adjust(2)
    # subjects_markup.row(InlineKeyboardButton(text='Отмена', callback_data='cancel'))

    msg = await call.message.edit_text('Выберите предмет: ')
    await call.message.edit_reply_markup(reply_markup=subjects_markup.as_markup())

    # await state.update_data({'msgs_to_delete': [msg.message_id]})

    await state.set_state(Bind.picked_subject)
    await call.answer()


@dp.callback_query(Bind.picked_subject)
async def state_Bind_picked_subject(call: CallbackQuery, state: FSMContext):
    if call.data == 'cancel':
        await cancel_state(state)
        await call.message.delete()
        await call.answer()
        return
    state_data = await state.get_data()
    await state.update_data({'subject': call.data})

    mgdz = ModernGDZ(call.from_user.id)
    sgdz = None
    if state_data['source'] == db.available_gdzs['gdz_putina']:
        sgdz = mgdz.GdzPutinaFun()
    subject_url = await sgdz.get_subject_url(state_data['grade'], call.data)
    books_data = await sgdz.get_books(subject_url)
    await state.update_data({'books_data': books_data})

    msgs_to_delete = []
    await call.message.delete()

    for i in range(0, len(books_data)):
        try:
            bmarkup = InlineKeyboardBuilder().add(InlineKeyboardButton(text='Выбрать', callback_data=str(i)))
            msg = await call.message.answer_photo(books_data[i]["img_url"],
                                                  caption=f'<b>{i + 1} / {len(books_data)}</b>. <a href="{books_data[i]["book_url"]}">{books_data[i]["img_title"]}</a>\n<code>{books_data[i]["author"]}</code>',
                                                  parse_mode=ParseMode.HTML, reply_markup=bmarkup.as_markup(),
                                                  disable_notification=True)
            msgs_to_delete.append(msg.message_id)
        except:
            print(books_data[i])
    await state.update_data({'msgs_to_delete': msgs_to_delete})
    await state.set_state(Bind.picked_book)
    await call.answer()


@dp.callback_query(Bind.picked_book)
async def state_Bind_picked_book(call: CallbackQuery, state: FSMContext, bot: Bot):
    state_data = await state.get_data()
    await state.update_data({'book_url': state_data['books_data'][int(call.data)]['book_url']})

    msg = await call.message.answer(
        'Введите alias для этого предмета:\nНапример: <code>алг</code> (пример поиска номера: <i>алг 135</i>). <i>алг</i> - это '
        'alias для вашего предмета, <i>135</i> это номер задания и тп. ',
        parse_mode=ParseMode.HTML, reply_markup=await cancel_markup())

    msgs_to_delete = state_data['msgs_to_delete']
    for msg_ in msgs_to_delete:
        await bot.delete_message(call.message.chat.id, msg_)
    await state.update_data({'msgs_to_delete': [msg.message_id]})

    await state.set_state(Bind.picked_alias)
    await call.answer()


@dp.message(Command('aliases'))
async def aliases(message: Message, state: FSMContext):
    await message.delete()
    al_text = await command_alias(message.from_user.id)
    if len(al_text[0]) == 0:
        await message.answer('У вас нет alias\'ов! Добавить --> /bind')
        return
    await message.answer(f'<b>Список alias\'ов:\nНажать для удаления.</b>\n{al_text[0]}',
                         reply_markup=al_text[1].as_markup(), disable_web_page_preview=True)


@dp.message(Command('kit'))
async def kit(message: Message, command: CommandObject):
    if command.args == '11':
        await message.delete()
        kit11 = {"алг": "https://gdz-putina.fun/klass-11/algebra/alimov",
                 "анг": "https://gdz-putina.fun/klass-11/anglijskij-yazyk/spotlight-evans",
                 "ерш": "https://gdz-putina.fun/klass-10/algebra/samostoyatelnie-i-kontrolnie-raboti-ershova",
                 "геом": "https://gdz-putina.fun/klass-11/geometriya/atanasyan"}
        await sql.change_data_jsonb(message.from_user.id, 'aliases', kit11)
        msg = await message.answer('Готово!')

        await asyncio.sleep(3)
        await msg.delete()


@dp.message(Command('wordcloud_settings'))
async def wordcloud_settings(message: Message, state: FSMContext):
    await cancel_state(state)
    await sql.add_wordcloud_user(user_id=message.from_user.id)
    current_settings = await sql.get_wordcloud_settings(user_id=message.from_user.id)
    settings_text = ''
    for k, v in current_settings.items():
        settings_text += f'{hbold(k)} - {hcode(v)}\n'
    await message.answer(settings_text, parse_mode=ParseMode.HTML)
    await message.answer(
        '<b>Отправьте сообщение выше по образцу для изменения настроек.</b>\n<a href="https://kristendavis27.medium.com/wordcloud-style-guide-2f348a03a7f8">colormap list</a>',
        parse_mode=ParseMode.HTML)
    await state.set_state(WordCloud.settings_input)


@dp.message(WordCloud.settings_input)
async def WordCloud_settings_input(message: Message, state: FSMContext):
    text = message.text.lower()
    # input_data = {}
    for line in text.split('\n'):
        k, v = line.split(' - ', 1)
        if v == 'none':
            await sql.change_data_type(message.from_user.id, k, 'NULL', 'wordcloud_settings')
        elif isinstance(v, str):
            await sql.change_data(message.from_user.id, k, v, 'wordcloud_settings')
        else:
            await sql.change_data_type(message.from_user.id, k, v, 'wordcloud_settings')
    await message.answer('Успешно!')
    await cancel_state(state)


@dp.message(Command('author'))
async def author(message: Message):
    await message.answer(f'Папа: {hlink("Александр", "https://t.me/DWiPok")}'
                         f'\nИсходный код: {hlink("Github", "https://github.com/DarkWood312/StudyBot")}',
                         parse_mode=ParseMode.HTML)
    await message.delete()


@dp.message(Command('docs'))
async def documents(message: Message):
    inline_kb = InlineKeyboardBuilder()
    ershov_button = InlineKeyboardButton(text='Сборник Ершова.pdf', callback_data='docs_ershov')
    ershovg_button = InlineKeyboardButton(text='Сборник Ершова Геометрия.pdf', callback_data='docs_ershovg')
    yashenko_matem_button = InlineKeyboardButton(text='Ященко (Математика ЕГЭ) 2024 36 вариантов.pdf',
                                                 callback_data='docs_yashenkomatem')
    inline_kb.add(ershov_button, ershovg_button, yashenko_matem_button)
    inline_kb.adjust(1)
    await message.answer('<b>Документы: </b>', reply_markup=inline_kb.as_markup())
    await message.delete()


@dp.message(F.text)
async def other_messages(message: Message):
    await sql.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name,
                       message.from_user.last_name)
    await sql.add_wordcloud_user(user_id=message.from_user.id)
    low = message.text.lower()
    # gdz = GDZ(message.from_user.id)

    if 'сжатие' in low:
        await sql.change_data_type(message.from_user.id, 'upscaled',
                                   False if await sql.get_data(message.from_user.id, 'upscaled') is True else True)
        await message.answer(
            f'Отправка фотографий с сжатием {"выключена" if await sql.get_data(message.from_user.id, "upscaled") == True else "включена"}!',
            reply_markup=await menu_markup(message.from_user.id))
    elif 'закончить' in low:
        await message.delete()
        await main_message(message)
    elif len(low) >= 50:
        text_data = await text_analysis(message.text, user_id=message.from_user.id)
        aow = text_data['amount_of_words']
        aos = text_data['amount_of_sentences']
        aoc = text_data['amount_of_chars']
        aocws = text_data['amount_of_chars_without_space']
        image = text_data['image']
        answer_text = f'<b>Количество слов:</b> <code>{aow}</code>\n<b>Количество предложений:</b> <code>{aos}</code>\n<b>Количество символов:</b> <code>{aoc}</code> (<code>{aocws}</code> без пробелов)'
        if image is not None:
            await message.answer_photo(BufferedInputFile(image.getvalue(), filename='image.png'), caption=answer_text,
                                       parse_mode=ParseMode.HTML)
        else:
            await message.answer(answer_text, parse_mode=ParseMode.HTML)

    else:
        aliases_dict = await sql.get_data(message.from_user.id, 'aliases')
        args = low.split(' ')
        # await message.answer(str(aliases))
        # await message.answer(str(args))
        if args[0] in aliases_dict:
            if len(args) > 2:
                var = args[1]
                if '-' in var:
                    f, s = var.split('-')
                    vars_list = [*range(int(f.strip()), int(s.strip()) + 1)]
                elif ',' in var:
                    vars_list = var.split(',')
                    vars_list = list(dict.fromkeys([int(i.strip()) for i in vars_list]))
                else:
                    vars_list = [var]
            mgdz = ModernGDZ(message.from_user.id)
            gdzput = mgdz.GdzPutinaFun()
            try:
                destination_url = str(aliases_dict[args[0]])
                task_groups = await gdzput.get_task_groups(destination_url)
                if len(args) < 3:
                    err1 = f'<b>Неправильно введены аргументы!</b>\nПример: <code>{args[0]} {args[1] if len(args) > 1 else "100"}</code> <i>(номер задания)</i>'
                    err1 = err1 + ' <code>1</code> <i>(номер группы)</i>\n<b>Доступные номера групп:</b>\n' + f'\n'.join(
                        f'<b>{c + 1}</b>. <code>{d}: {" | ".join(list(task_groups[d].keys())[:4])}</code>...' for c, d
                        in enumerate(list(task_groups.keys())))
                    await message.answer(err1)
                    return
                # if len(task_groups) == 1:
                #     imgs = await gdzput.gdz(destination_url, args[1])
                else:
                    # if len(args) < 3:
                    #     await message.answer(f'<b>Нужно указать номер группы заданий!</b>\nПример: <code>{args[0]} {args[1]} 1</code> <i>(номер группы)</i>\n<b>Доступные номера групп:</b>\n' + f'\n'.join(f'<b>{c+1}</b>. <code>{d}: {" | ".join(list(task_groups[d].keys())[:4])}</code>...' for c, d in enumerate(list(task_groups.keys()))))
                    #     return
                    # await message.answer(str(list(task_groups.keys())))
                    for v in vars_list:
                        imgs = await gdzput.gdz(destination_url, v, list(task_groups.keys())[int(args[2]) - 1])
                        if await sql.get_data(message.from_user.id, "upscaled") == 1:
                            inputs = [InputMediaDocument(media=i) for i in imgs]
                        else:
                            inputs = [InputMediaPhoto(media=i) for i in imgs]
                        inputs = [inputs[i:i + 10] for i in range(0, len(inputs), 10)]
                        for input_ in inputs:
                            media_group = MediaGroupBuilder(caption=f'<a href="{destination_url}">{v}</a>',
                                                            media=input_)
                            await message.answer_media_group(media_group.build())
            except TypeError as e:
                await message.answer('Номер не найден!')
                print(e)
            except Exception as e:
                print(e)

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


@dp.message(IsAdmin())
async def other_content_admin(message: Message):
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


@dp.message()
async def other_content(message: Message):
    await message.answer('Я еще не настолько умный')


@dp.callback_query()
async def callback(call: CallbackQuery, state: FSMContext):
    if call.data == 'cancel':
        await cancel_state(state)
        await call.message.answer('Действие отменено.')
    elif call.data.startswith('alias_del'):
        param = call.data.replace('alias_del-', '')

        old_data = dict(await sql.get_data(call.from_user.id, 'aliases'))
        old_data.pop(param)

        await sql.change_data_jsonb(call.from_user.id, 'aliases', old_data)
        await call.answer(f'Alias \'{param}\' успешно удален!')

        al_text = await command_alias(call.from_user.id)
        await call.message.edit_text(f'<b>Список alias\'ов:\nНажать для удаления.</b>\n{al_text[0]}',
                                     reply_markup=al_text[1].as_markup(), disable_web_page_preview=True)
    elif call.data.startswith('docs_'):
        param = call.data.replace('docs_', '')

        await call.message.answer_document(db.doc_ids[param])

    # elif call.data == 'algm':
    #     await call.message.answer_document(db.doc_ids['algm'])
    elif call.data.startswith(tuple(['2', '3', '4', '5'])):
        call.message.text = call.data
        # await call.message.answer(call.message.text)
        await average_mark(message=call.message, state=state)
    await call.answer()


async def main():
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(token, parse_mode=ParseMode.HTML)
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    nltk.download('punkt')
    nltk.download('stopwords')
    asyncio.run(main())
