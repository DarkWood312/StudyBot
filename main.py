import asyncio
import re
from datetime import datetime
from random import shuffle

import cryptography.fernet
import httpx
# import nltk
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ChatAction
from aiogram.filters import Filter, Command, CommandStart, CommandObject
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import CallbackQuery, InputMediaPhoto, InputMediaDocument, BufferedInputFile
from aiogram.utils.markdown import hbold, hcode, hlink
from aiogram.utils.media_group import MediaGroupBuilder
from redis.asyncio.client import Redis
from chatgpt_md_converter import telegram_format
# from ai_deprecated.ai_deprecated import AI, text2text, text2image, image2image, GigaAI, ai_func_start
from extra.config import *
from extra.keyboards import *
from extra.states import *
from extra.utils import *
from gdz.modern_gdz import ModernGDZ
from uchus_online.uchus_online import UchusOnline, Task
from AI.AI import VisionAI, TrueOpenAI, ai2text

# from typing import TextIO

if redis_host:
    dp = Dispatcher(storage=RedisStorage(Redis(host=redis_host, port=redis_port, password=redis_password)))
    logger.success('The bot is running on Redis! :)')
else:
    dp = Dispatcher(storage=MemoryStorage())
    logger.warning('The bot is running on MemoryStorage!')


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
            await message.answer(str(e))
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
    msg = await message.answer('Возврат в меню.', reply_markup=await menu_markup(message.from_user.id))
    await message.delete()

    # await asyncio.sleep(2)
    # await msg.delete()


@dp.message(CommandStart())
async def start_message(message: Message, state: FSMContext):
    await cancel_state(state)
    await init_user(message)
    await main_message(message)
    await message.delete()


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


@dp.message(Bind.picked_alias)
async def state_Bind_picked_alias(message: Message, state: FSMContext, bot: Bot):
    await state.update_data({'alias': message.text.split(' ')[0].lower()})
    state_data = await state.get_data()
    alias = state_data['alias']

    old_data = await sql.get_data(message.from_user.id, 'aliases')
    old_data[alias] = state_data['book_url']

    # await sql.change_data_jsonb(message.from_user.id, 'aliases', old_data)
    await sql.update_data(message.from_user.id, 'aliases', old_data)
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

        # # * Randoms
        # rand = random.randint(1, 100)
        # total_floor = 10
        # if rand <= 1.25 and total > 0:
        #     await message.answer_video_note(db.video_note_answers['nikita_lucky-1'])
        # elif 1.25 < rand <= 2.5 and total > 0:
        #     await message.answer_video_note(db.video_note_answers['nikita_lucky-2'])
        # elif 2.5 < rand <= 3.75 and total > 0:
        #     await message.answer_video_note(db.video_note_answers['nikita_lucky-3'])
        # elif 3.75 < rand <= 5 and total > 0:
        #     await message.answer_video_note(db.video_note_answers['nikita_lucky-4'])
        # elif percentage == 100 and total == 1:
        #     await message.answer_video_note(db.video_note_answers['nikita_fake_100-1'])
        # elif percentage == 0 and total == 1:
        #     await message.answer_video_note(db.video_note_answers['nikita_fake_100-2'])
        # elif percentage == 0 and total >= total_floor:
        #     if rand <= 25:
        #         await message.answer_video_note(db.video_note_answers['nikita_fu-2'])
        #         await message.answer_video_note(db.video_note_answers['nikita_fu-3'])
        #     else:
        #         await message.answer_video_note(db.video_note_answers['nikita_fu-1'])
        # elif percentage <= 10 and total >= total_floor:
        #     if rand <= 10:
        #         await message.answer_video_note(db.video_note_answers['nikita_less10-2'])
        #     else:
        #         await message.answer_video_note(db.video_note_answers['nikita_less10-1'])
        # elif 80 > percentage >= 50 and total >= total_floor:
        #     await message.answer_video_note(db.video_note_answers['nikita_mid-1'])
        # elif 90 > percentage >= 80 and total >= total_floor:
        #     await message.answer_video_note(db.video_note_answers['nikita_high-1'])
        # elif 100 > percentage >= 90 and total >= total_floor:
        #     await message.answer_video_note(db.video_note_answers['nikita_high-2'])
        # elif percentage == 100 and total >= len(words):
        #     await message.answer_video_note(db.video_note_answers['holid_100-1'])


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

        if letter.lower() in constants.gl:
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

    gls = [letter.lower() for letter in words[pos] if letter.lower() in constants.gl]
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
    with open('extra/test_settings.txt') as f:
        settings = {}
        for line in f.readlines():
            line = line.strip()
            p = line.split('=')
            settings[p[0]] = int(p[1]) if p[1].isdigit() else p[1]
    await state.update_data(
        {'user_credentials': [message.text, message.from_user.id], 'test_mode': True, 'test_settings': settings})
    await orthoepy(message, state, test_mode=settings)


@dp.message(AiState.choose)
async def AiState_choose(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await bot.delete_message(message.chat.id, data['delete_this_msg'].message_id)
    if 'Отмена❌' in message.text:
        # await cancel_state(state)
        # await message.delete()
        # await message.answer('Действие отменено.', reply_markup=await menu_markup(message.from_user.id))
        await cancel(message, state)
    else:
        markup = ReplyKeyboardBuilder().row(KeyboardButton(text='Закончить разговор❌')).as_markup(resize_keyboard=True,
                                                                                                  one_time_keyboard=True)
        await message.delete()
        if 'LLM' in message.text:
            llms = await VisionAI.get_llm_models()
            await message.answer(
                '\n'.join(f"<b>{i}</b>. <code>{model}</code>" for i, model in enumerate(llms, start=1)),
                reply_markup=markup)
            await state.set_state(AiState.llm_choose)
        elif 'Dalle' in message.text:
            await state.set_state(AiState.dalle)
            await message.answer('Пишите ваш запрос.', reply_markup=markup)
        elif 'Stable Diffusion models' in message.text:
            pass
        elif 'Text2GIF' in message.text:
            await state.set_state(AiState.text2gif)
            await message.answer('Пишите ваш запрос.', reply_markup=markup)
        elif 'GPT 4' in message.text and (await sql.get_data(message.from_user.id, 'ai_access')) == True:
            await state.set_state(AiState.openai_chat)
            await message.answer('Пишите ваш запрос.', reply_markup=markup)
        elif 'true dalle' in message.text.lower() and (await sql.get_data(message.from_user.id, 'ai_access')) == True:
            await state.set_state(AiState.openai_dalle)
            await message.answer('Пишите ваш запрос.', reply_markup=markup)

        else:
            await message.answer('Нажмите кнопку')
            return


@dp.message(AiState.llm_choose)
async def AiState_llm_choose(message: Message, state: FSMContext):
    if message.text == 'Закончить разговор❌':
        await cancel(message, state)
        return

    llms = await VisionAI.get_llm_models()
    model = llms[int(message.text) - 1]
    await message.answer(f'<b>Выбранная модель:</b> <code>{model}</code>\nПишите ваш запрос.')
    await state.update_data({'model': model, 'messages': None})
    await state.set_state(AiState.llm)


@dp.message(AiState.llm)
async def AiState_llm(message: Message, state: FSMContext, bot: Bot):
    if message.text == 'Закончить разговор❌':
        await cancel(message, state)
        return
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    data = await state.get_data()
    ai = VisionAI(visionai_api)
    try:
        response = await ai.llm(message.text, model=data['model'], messages=data['messages'])
        chunks = await ai2text(response, model=data['model'])
        for chunk in chunks:
            await message.answer(chunk)

        await state.update_data({'messages': response.messages})

    except Exception as e:
        logger.error(f'VisionAI error! {e}')
        await message.answer(f'Ошибка. Попробуйте позже или другую модель.\n{e}')


@dp.message(AiState.dalle)
async def AiState_dalle(message: Message, state: FSMContext, bot: Bot):
    if message.text == 'Закончить разговор❌':
        await cancel(message, state)
        return
    await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)

    tr = Translation(deep_translate_api)
    text = await tr.translate(message.text, 'en', await tr.detect(message.text))

    ai = VisionAI(visionai_api)
    try:
        image = await ai.generate_image(text)
        caption = f'<b>Dall-E</b>🦋: <code>{html.quote(text[600:])}</code>'
        await message.answer_photo(BufferedInputFile(image.getvalue(), 'generated_image.png'),
                                   caption=caption)
        await message.answer_document(BufferedInputFile(image.getvalue(), 'generated_image.png'))

    except Exception as e:
        logger.error(f'VisionAI error! {e}')
        await message.answer(f'Ошибка. Попробуйте позже или другую модель.\n{e}')


@dp.message(AiState.text2gif)
async def AiState_text2gif(message: Message, state: FSMContext, bot: Bot):
    if message.text == 'Закончить разговор❌':
        await cancel(message, state)
        return
    await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)

    tr = Translation(deep_translate_api)
    text = await tr.translate(message.text, 'en', await tr.detect(message.text))

    ai = VisionAI(visionai_api)
    try:
        gif = (await ai.generate_gif(text))[0]

        await message.answer_animation(BufferedInputFile(gif.getvalue(), 'generated_gif.gif'),
                                       caption=f'<b>Text2Gif</b>🎞️: <code>{html.quote(text)}</code>')
    except Exception as e:
        logger.error(f'VisionAI error! {e}')
        await message.answer(f'Ошибка. Попробуйте позже или другую модель.\n{e}')


@dp.message(AiState.openai_chat)
async def AiState_openai_chat(message: Message, state: FSMContext, bot: Bot):
    if message.text == 'Закончить разговор❌':
        await cancel(message, state)
        return
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    ai = TrueOpenAI(openai_api)

    image = None
    if message.photo:
        image = (await bot.download(message.photo[-1].file_id)).read()
    try:
        response = await ai.chat(message.text or message.caption or "", image=image)
        logger.debug(response)
        chunks = await ai2text(response, model='GPT 4o')
        for chunk in chunks:
            await message.answer(chunk)

        await state.update_data({'messages': response.messages})

        tokens = await sql.get_data(message.from_user.id, 'openai_tokens')
        await sql.update_data(message.from_user.id, 'openai_tokens', tokens + response.tokens)

    except Exception as e:
        logger.error(f'OpenAI error! {e}')
        await message.answer(f'Ошибка. \n{e}')


@dp.message(AiState.openai_dalle)
async def AiState_openai_dalle(message: Message, state: FSMContext, bot: Bot):
    if message.text == 'Закончить разговор❌':
        await cancel(message, state)
        return
    await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)

    tr = Translation(deep_translate_api)
    text = await tr.translate(message.text, 'en', await tr.detect(message.text))

    ai = TrueOpenAI(openai_api)
    try:
        image, revised_prompt = await ai.generate_image(text)
        caption = f'<b>True Dall-E</b>🦋: <code>{html.quote(text[:300])}</code>\n\n<tg-spoiler><code>{revised_prompt[:300]}</code></tg-spoiler>'
        await message.answer_photo(BufferedInputFile(image.getvalue(), 'generated_image.png'),
                                   caption=caption)
        await message.answer_document(BufferedInputFile(image.getvalue(), 'generated_image.png'))

    except Exception as e:
        logger.error(f'OpenAI error! {e}')
        await message.answer(f'Ошибка. Попробуйте позже или другую модель.\n{e}')


# @dp.message(AiState.chatgpt_turbo)
# async def chatgpt_turbo_st(message: Message, state: FSMContext, bot: Bot):
#     async with aiohttp.ClientSession() as session:
#         await text2text(message, state, bot, 'gpt-3-5-turbo', 'ChatGPT-Turbo', session)


# @dp.message(AiState.gemini_pro)
# async def gemini_pro_st(message: Message, state: FSMContext, bot: Bot):
#     async with aiohttp.ClientSession() as session:
#         await text2text(message, state, bot, 'gemini-pro', 'Gemini-Pro', session)
#
#
# @dp.message(AiState.midjourney_v4)
# async def midjourney_v4_st(message: Message, state: FSMContext, bot: Bot):
#     async with aiohttp.ClientSession() as session:
#         ai_deprecated = AI(session)
#         await text2image(message, state, bot, ai_deprecated.midjourney_v4, 'Midjourney-V4')
#
#
# @dp.message(AiState.midjourney_v6)
# async def midjourney_v6_st(message: Message, state: FSMContext, bot: Bot):
#     async with aiohttp.ClientSession() as session:
#         ai_deprecated = AI(session)
#         await text2image(message, state, bot, ai_deprecated.midjourney_v6, 'Midjourney-V6')
#
#
# @dp.message(AiState.playground_v2)
# async def playground_v2_st(message: Message, state: FSMContext, bot: Bot):
#     async with aiohttp.ClientSession() as session:
#         ai_deprecated = AI(session)
#         await text2image(message, state, bot, ai_deprecated.playgroundv2, 'Playground-V2')
#
#
# @dp.message(AiState.stable_diffusion_xl_turbo)
# async def stable_diffusion_xl_turbo_st(message: Message, state: FSMContext, bot: Bot):
#     async with aiohttp.ClientSession() as session:
#         ai_deprecated = AI(session)
#         await text2image(message, state, bot, ai_deprecated.stable_diffusion_xl_turbo, 'Stable Diffusion XL Turbo')
#
#
# @dp.message(AiState.claude)
# async def claude_st(message: Message, state: FSMContext, bot: Bot):
#     async with aiohttp.ClientSession() as session:
#         await text2text(message, state, bot, 'claude-instant', 'Claude', session)
#
#
# @dp.message(AiState.mistral_medium)
# async def mistral_medium_st(message: Message, state: FSMContext, bot: Bot):
#     async with aiohttp.ClientSession() as session:
#         # ai_deprecated = AI(session)
#         await text2text(message, state, bot, 'mistral-medium', 'Mistral Medium', session)
#
#
# @dp.message(AiState.gigachat)
# async def gigachat_st(message: Message, state: FSMContext, bot: Bot):
#     if not await ai_func_start(message, state, bot, 'typing'):
#         await cancel(message, state)
#         return
#
#     data = await state.get_data()
#     async with aiohttp.ClientSession() as session:
#         giga = GigaAI(session)
#         access_token = await giga.access_token
#         if 'giga_messages' not in data:
#             giga_messages = []
#         else:
#             giga_messages = data['giga_messages']
#         giga_messages.append({'role': 'user', 'content': message.text})
#
#         answer, imgs = await giga.chat(access_token, giga_messages)
#         giga_messages.append({'role': 'assistant', 'content': answer})
#         await state.update_data({'giga_messages': giga_messages})
#         if len(imgs) > 0:
#             await message.answer_media_group(media=[InputMediaPhoto(media=BufferedInputFile(img, filename='photo.jpg'),
#                                                                     caption='<b>GigaChat💬:</b>' + html.quote(answer),
#                                                                     parse_mode=ParseMode.HTML) for img in imgs])
#         else:
#             await message.answer('<b>GigaChat💬:</b>' + html.quote(answer), parse_mode=ParseMode.HTML)
#
#
# # @dp.message(AiState.dalle3)
# # async def dalle3_st(message: Message, state: FSMContext, bot: Bot):
# #     async with aiohttp.ClientSession() as session:
# #         ai_deprecated = AI(session)
# #         await text2image(message, state, bot, ai_deprecated.dalle3, 'Dall-E 3')
#
#
# @dp.message(AiState.photomaker)
# async def photomaker_st(message: Message, state: FSMContext, bot: Bot):
#     async with aiohttp.ClientSession() as session:
#         ai_deprecated = AI(session)
#         await image2image(message, state, bot, ai_deprecated.photomaker, 'Photomaker')
#
#
# @dp.message(AiState.hcrt)
# async def hcrt_st(message: Message, state: FSMContext, bot: Bot):
#     async with aiohttp.ClientSession() as session:
#         ai_deprecated = AI(session)
#         await image2image(message, state, bot, ai_deprecated.hcrt, 'High-Resolution-Controlnet-Tile')


@dp.message(Command('wolfram'))
async def wolfram_command(message: Message, state: FSMContext):
    await message.delete()
    await cancel_state(state)
    msg = await message.answer('Введите ваш запрос:', reply_markup=await reply_cancel_markup())
    await state.set_state(WolframState.main)
    await state.update_data({'delete_this_msgs': [msg]})


@dp.message(WolframState.main)
async def wolfram_msg_main_st(message: Message, state: FSMContext, bot: Bot):
    if 'закончить' in message.text.lower():
        await cancel_state(state)
        await message.delete()
        await message.answer('Возврат в меню.', reply_markup=await menu_markup(message.from_user.id))
        return

    text = message.text
    translator = Translation(deep_translate_api)
    source_lang = await translator.detect(text)
    if source_lang != 'en':
        text = await translator.translate(text, 'en', source_lang)

    await bot.send_chat_action(message.chat.id, 'upload_photo')
    try:
        image = (await wolfram_getimg(wolfram_api, text, 'image'))[1]
        await message.answer_photo(
            BufferedInputFile(image, filename=f"wolfram_{datetime.now().strftime('%d-%m--%H-%M-%S')}.png"),
            caption=f'<b>Wolfram</b>📙: <code>{text}</code>')

    except WolframException.NotSuccess:
        await message.answer('Ошибка. Попробуйте уточнить запрос.')
    return


@dp.message(UchusOnlineState.ans)
async def state_uchusonline_ans(message: Message, state: FSMContext):
    if message.text == 'Закончить❌':
        await cancel(message, state)
        return

    task: Task = (await state.get_data())['task']
    async with aiohttp.ClientSession() as session:
        uo = UchusOnline(session, uchus_cookies)
        res: bool = await uo.answer(task.id, message.text)

    add_text = f'\n<b>{html.quote(">>")}</b> <a href="{task.resolution}">Решение</a> <b>{html.quote("<<")}</b>'
    if res:
        await message.answer('<b>Правильно!</b>' + add_text)
        current: list = await sql.get_data(message.from_user.id, 'done', 'uchus_online')
        current.append(task.id)
        await sql.update_data(message.from_user.id, 'done', current, 'uchus_online')
    if not res:
        await message.answer('<b>Неправильно!</b>' + add_text)


@dp.message(UchusOnlineState.change_diff)
async def state_uchusonline_change_diff(message: Message, state: FSMContext):
    data = await state.get_data()
    msg_to_edit: Message = data['msg_to_edit']
    msg_to_remove: Message = data['msg_to_remove']
    params = list(map(int, message.text.split(' ', 1)))
    from_, to_ = (min(params), max(params))
    # await sql.change_data_type(message.from_user.id, 'min_complexity', from_, 'uchus_online')
    await sql.update_data(message.from_user.id, 'min_complexity', from_, 'uchus_online')
    # await sql.change_data_type(message.from_user.id, 'max_complexity', to_, 'uchus_online')
    await sql.update_data(message.from_user.id, 'max_complexity', to_, 'uchus_online')

    await msg_to_edit.edit_reply_markup(reply_markup=await uchus_online_settings_markup(message.from_user.id))
    await state.set_state(UchusOnlineState.choose)

    await message.delete()
    await msg_to_remove.delete()


@dp.message(Command('encryption', 'en'))
async def encryption_command(message: Message, state: FSMContext):
    markup = InlineKeyboardBuilder()
    markup.row(InlineKeyboardButton(text='Зашифровать', callback_data='encryption_encrypt'))
    markup.row(InlineKeyboardButton(text='Расшифровать', callback_data='encryption_decrypt'))
    await message.answer('<b>Выберите действие: </b>', reply_markup=markup.as_markup())
    await message.delete()


@dp.message(EncryptionState.encrypt_st)
async def encryption_encrypt_state(message: Message, state: FSMContext):
    if message.text == 'Закончить❌':
        await cancel(message, state)
        return
    msgs_to_del = (await state.get_data())['delete_this_msgs']
    msg = await message.answer('<b>Введите ключ для расшифровки в будущем: </b> (на английском без спец. символов)')
    await state.update_data({'text': message.text, 'method': 'encrypt', 'delete_this_msgs': msgs_to_del + [msg]})
    await state.set_state(EncryptionState.final_st)

    await message.delete()


@dp.message(EncryptionState.decrypt_st)
async def encryption_decrypt_state(message: Message, state: FSMContext):
    if message.text == 'Закончить❌':
        await cancel(message, state)
        return
    msgs_to_del = (await state.get_data())['delete_this_msgs']
    await state.update_data({'text': message.text, 'method': 'decrypt'})
    msg = await message.answer('<b>Введите ключ для расшифровки: </b> (на английском без спец. символов)')
    await state.set_state(EncryptionState.final_st)

    await message.delete()
    await state.update_data({'delete_this_msgs': msgs_to_del + [msg]})


@dp.message(EncryptionState.final_st)
async def encryption_final_state(message: Message, state: FSMContext):
    if message.text == 'Закончить❌':
        await cancel(message, state)
        return
    data = await state.get_data()
    method = data['method']
    text = data['text']
    key = message.text
    enc = Encryption(key)
    try:
        if method == 'encrypt':
            result = await enc.encrypt(text)
        else:
            try:
                result = await enc.decrypt(text)
            except cryptography.fernet.InvalidToken or cryptography.fernet.InvalidSignature:
                await message.answer('Неверный ключ или шифр!')
                return

        await message.answer(
            f'<b>Результат:</b> <code>{html.quote(result)}</code>\n<b>Ключ:</b> <code>{html.quote(key)}</code>')
        await cancel_state(state)

    except ValueError:
        await message.answer('Ключ должен быть на английском языке без спец. символов!')
    await message.delete()


@dp.message(Command('ege_points', 'ep'))
async def ege_points_cmd(message: types.Message):
    await message.delete()
    args = message.text.split(' ')
    try:
        if len(args) > 1:
            text = f'<b>{args[1]} первичных баллов --> </b>\n'
            subjects = constants.subjects
            res = await ege_points_converter(int(args[1]), 'all')
            text += '\n'.join(f'<code>{subjects[k].capitalize()}</code>: <b>{v}</b>' for k, v in res.items())
            await message.answer(
                text + '\n\n<a href="https://docs.google.com/spreadsheets/d'
                       '/1FcMBx2UpSEwTuYUgvLQUnhm9VfuGgSKXLbxJdGjTQfY/edit?usp=sharing">Таблица</a>',
                disable_web_page_preview=True)
            return
        await message.answer(f'<b>Использование:</b> /ep {html.quote("<кол-во первичных баллов>")}')
    except IndexError:
        await message.answer('-')


@dp.message(Command('base_converter', 'ba', 'bc'))
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
        finished = await message.answer('Готово!', reply_markup=await menu_markup(message.from_user.id))
        await cancel_state(state)
        await asyncio.sleep(1)
        await finished.delete()
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
        await message.answer(
            f"<b>Ошибка</b>: Значениe '<code>{e.args[1]}</code>' не существуют в СС с основанием '<code>{e.args[2]}</code>'",
            parse_mode=ParseMode.HTML)
        return
    except BaseDontExistError:
        await message.answer('<b>Ошибка</b>: СС с основанием > <code>36</code>', parse_mode=ParseMode.HTML)
        return
    text = bytes(
        fr'{hcode(num)}\u208' + fr'\u208'.join([*str(from_base)]) + fr' --> {hcode(conv)}\u208' + r'\u208'.join(
            [*str(to_base)]), 'utf-8').decode('unicode_escape')
    await message.answer(text, parse_mode=ParseMode.HTML)


@dp.message(RootExtr.init)
async def state_rootextr_main(message: Message, state: FSMContext):
    ans = message.text
    await message.delete()
    data = await state.get_data()

    if 'закончить' in message.text.lower():
        await cancel_state(state)
        await message.answer('Готово!', reply_markup=await menu_markup(message.from_user.id))
        return

    if not re.compile('^[0-9]+ [0-9]+$').match(ans):
        await message.answer('Некорректно введены границы')
        return

    borders = list(map(int, message.text.split(' ', 1)))
    range_ = list(range(min(borders) if min(borders) > 0 else 1, (max(borders) + 1) if max(borders) <= 1000 else 1001))

    await state.update_data({'range': range_, 'overall': 0, 'right': 0})

    msgd = await message.answer(await root_extraction_formatting(state))

    await state.update_data({'delete_this_msgs': data['delete_this_msgs'] + [msgd]})
    await state.set_state(RootExtr.main)


@dp.message(RootExtr.main)
async def state_rootextr_main(message: Message, state: FSMContext):
    data = await state.get_data()
    if 'закончить' in message.text.lower() or len(data['range']) == 0:
        await message.delete()
        await message.answer(
            f'<b>Статистика по извлечению корня:</b>\n<i>Всего</i> - <code>{data["overall"]}</code>\n<i>Правильных</i> - <code>{data["right"]}</code>\n<i>Неправильных</i> - <code>{data["overall"] - data["right"]}</code>\n<i>В процентах</i> - <code>{(data["right"] / data["overall"] * 100 if data["overall"] != 0 else 0):.2f}%</code>',
            reply_markup=await menu_markup(message.from_user.id))
        await cancel_state(state)
        return

    is_right = False
    if message.text == str(data['solution']):
        rnr = await message.answer('Правильно!')
        is_right = True
    else:
        rnr = await message.answer(f'Неправильно!\nПравильный ответ: <code>{data["solution"]}</code>')

    msgd = await message.answer(await root_extraction_formatting(state))

    await state.update_data(
        {'overall': data['overall'] + 1, 'right': (data['right'] + 1) if is_right else data['right'],
         'delete_this_msgs': data['delete_this_msgs'] + [msgd, rnr, message]})


@dp.message(F.text.contains('2764'))
async def mpassword(message: Message):
    await message.answer(hcode('U+2764 U+FE0F U+200D U+1FA79'))


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
        # await call.message.answer('Действие отменено')
        await cancel(call.message, state)
    else:
        await cancel_state(state)
        await callback(call, state)
    await call.answer()


@dp.message(Command('bind'))
async def bind(message: Message, state: FSMContext):
    await cancel_state(state)

    source_markup = InlineKeyboardBuilder()
    for gdz_source in constants.available_gdzs.values():
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
        with open('extra/test_settings.txt') as f:
            await message.answer('\n'.strip().join(f.readlines()))
        return
    if len(params) != 3:
        await message.answer('Неправильное количество параметров!')
        return

    receiver = int(params[1])
    amount_of_words = int(params[2])
    with open('extra/test_settings.txt', 'w') as f:
        f.write(f'''receiver={receiver}\namount_of_words={amount_of_words}'''.strip())
    await message.answer('Done!')


# ! Disabled
# @dp.message(Command('test'))
# async def orthoepy_test(message: Message, state: FSMContext):
#     await cancel_state(state)
#     params = message.text.split(' ')
#
#     await message.answer('<b>Введите свои данные</b> (<i>например:</i> <code>Иванов А, 11Б</code>): ',
#                          parse_mode=ParseMode.HTML)
#     await state.set_state(Test.credentials)
#     if len(params) == 2:
#         if params[1] == 'ans!':
#             await state.update_data({'show_answers': True})


@dp.message(Command('orthoepy', 'or'))
async def orthoepy(message: Message, state: FSMContext, test_mode: bool | dict = False):
    if test_mode is False:
        await cancel_state(state)

    with open('extra/orthoepy.txt', encoding='utf-8') as f:
        words = [w.strip() for w in f.readlines()]
        shuffle(words)
    amount_of_words = len(words)
    if test_mode is not False:
        amount_of_words = test_mode['amount_of_words']

    gls = [letter.lower() for letter in words[0] if letter.lower() in constants.gl]

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


@dp.message(Command('root_extraction', 're', 'ro'))
async def root_extraction(message: Message, state: FSMContext):
    await cancel_state(state)
    await message.delete()

    msgd = await message.answer(
        '<b>Введите границы чисел (от 1 до 1000), которые будут возводиться в квадрат.</b> \n<i>Например:</i> <code>10 20</code> (=> нужно будет извлечь корень у чисел от 100 до 400)',
        reply_markup=await reply_cancel_markup())
    await state.set_state(RootExtr.init)
    await state.update_data({'delete_this_msgs': [msgd]})


@dp.message(Command('ostats', 'os'))
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
    if state_data['source'] == constants.available_gdzs['gdz_putina']:
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
        # await sql.change_data_jsonb(message.from_user.id, 'aliases', kit11)
        await sql.update_data(message.from_user.id, 'aliases', kit11)
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
            # await sql.change_data_type(message.from_user.id, k, 'NULL', 'wordcloud_settings')
            await sql.update_data(message.from_user.id, k, None, 'wordcloud_settings')
        elif isinstance(v, str):
            # await sql.update_data(message.from_user.id, k, v, 'wordcloud_settings')
            await sql.update_data(message.from_user.id, k, v, 'wordcloud_settings')
        else:
            # await sql.change_data_type(message.from_user.id, k, v, 'wordcloud_settings')
            await sql.update_data(message.from_user.id, k, v, 'wordcloud_settings')
    await message.answer('Успешно!')
    await cancel_state(state)


@dp.message(Command('formulas', 'f', 'fo'))
async def formulas_cmd(message: Message, state: FSMContext, msg_to_edit: Message = None):
    await cancel_state(state, False)
    async with aiohttp.ClientSession() as session:
        im = IndigoMath(session)
        fgroups = await im.formulas_groups()
    markup = InlineKeyboardBuilder().add(
        *[InlineKeyboardButton(text=b, callback_data=str(i)) for i, b in enumerate(fgroups.keys())]).adjust(1)
    if msg_to_edit is not None:
        fmsg = await msg_to_edit.edit_text(text='Выберите категорию: ', reply_markup=markup.as_markup())
    else:
        fmsg = await message.answer(text='Выберите категорию: ', reply_markup=markup.as_markup())
    await state.update_data({'fmsg': fmsg, 'fgroups': fgroups, 'delete_this_msgs': [fmsg]})
    await state.set_state(Formulas.formulas_list)
    if msg_to_edit is None:
        await message.delete()


@dp.callback_query(Formulas.formulas_list)
async def state_formulas_list(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    fgroup = list(data['fgroups'].values())[int(call.data)]
    await state.update_data({'fgroup': fgroup})
    markup = InlineKeyboardBuilder().add(
        *[InlineKeyboardButton(text=b, callback_data=str(i)) for i, b in enumerate(fgroup.keys())]).add(
        InlineKeyboardButton(text='Вернуться назад', callback_data='back')).adjust(1)
    await data['fmsg'].edit_text(text='Выберите тему: ', reply_markup=markup.as_markup())
    await state.set_state(Formulas.formulas_out)
    await call.answer()


@dp.callback_query(Formulas.formulas_out)
async def state_formulas_out(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if call.data == 'back':
        await formulas_cmd(call.message, state, data['fmsg'])
    else:
        fgroup = data['fgroup']
        async with aiohttp.ClientSession() as session:
            formulas = await IndigoMath(session).get_formulas(list(data['fgroup'].values())[int(call.data)])
        lines = [f'<a href="{formulas[f][2]}">{f}</a>' for f in formulas]
        chunks = await chunker(lines, 70)
        for chunk in chunks:
            await call.message.answer(
                f'<b>Формулы по запросу:</b> <i>{html.quote(list(fgroup.keys())[int(call.data)])}</i> <b>({len(formulas)})</b>\n' + '\n'.join(
                    chunk), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        await call.answer()


@dp.message(Command('ai'))
async def ai_command(message: Message, state: FSMContext, command: CommandObject):
    if (command.args is not None) and (await sql.get_data(message.from_user.id, 'admin')):
        if command.args.startswith('-'):
            # await sql.change_data_type(command.args[1:], 'ai_access', False)
            await sql.update_data(command.args[1:], 'ai_access', False)
            await message.answer(f'{command.args[1:]} потерял доступ к AI')
        else:
            # await sql.change_data_type(command.args, 'ai_access', True)
            await sql.update_data(command.args, 'ai_access', True)
            await message.answer(f'{command.args} получил доступ к AI')
        return
    if not (await sql.get_data(message.from_user.id, 'ai_access')):
        await message.answer('У вас нет доступа к этой функции.')
        return
    msg = await message.answer('Выберите AI', reply_markup=await visionai_markup())
    await state.update_data({'delete_this_msg': msg})
    await state.set_state(AiState.choose)


@dp.message(Command('uchus'))
async def uchus_command(message: Message, state: FSMContext):
    await cancel_state(state)
    await message.answer('Выберите категорию: ', reply_markup=await uchus_online_markup())
    await state.set_state(UchusOnlineState.choose)


@dp.message(UchusOnlineState.choose)
async def state_uchusonline_choose(message: Message, state: FSMContext):
    if 'закончить' in message.text.lower():
        await cancel(message, state)
        return

    await message.delete()
    if 'задания' in message.text.lower():
        async with aiohttp.ClientSession() as session:
            uo = UchusOnline(session, uchus_cookies)
            topics = await uo.get_banks_id()
        markup = InlineKeyboardBuilder()
        for topic in topics:
            markup.row(InlineKeyboardButton(text=topic, callback_data=f'uchus_{topic[:3]}'))
        await message.answer('Выберите группу заданий:', reply_markup=markup.as_markup())
    elif 'настройки' in message.text.lower():
        await message.answer('<b>Ваши настройки:</b>',
                             reply_markup=await uchus_online_settings_markup(message.from_user.id))


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
async def other_messages(message: Message, bot: Bot, state: FSMContext):
    await init_user(message)
    # if (message.chat.type == 'group' and message.text.startswith('std')) or message.chat.type != 'group'
    low = message.text.lower()
    # gdz = GDZ(message.from_user.id)

    if 'сжатие' in low:
        # await sql.change_data_type(message.from_user.id, 'upscaled', False if await sql.get_data(message.from_user.id, 'upscaled') is True else True)
        await sql.update_data(message.from_user.id, 'upscaled',
                              False if await sql.get_data(message.from_user.id, 'upscaled') is True else True)
        await message.answer(
            f'Отправка фотографий с сжатием {"выключена" if await sql.get_data(message.from_user.id, "upscaled") == True else "включена"}!',
            reply_markup=await menu_markup(message.from_user.id))
    # elif len(low) >= 50:
    #     await bot.send_chat_action(message.chat.id, 'typing')
    #     text_data = await text_analysis(message.text, user_id=message.from_user.id)
    #     aow = text_data['amount_of_words']
    #     aos = text_data['amount_of_sentences']
    #     aoc = text_data['amount_of_chars']
    #     aocws = text_data['amount_of_chars_without_space']
    #     image = text_data['image']
    #     answer_text = f'<b>Количество слов:</b> <code>{aow}</code>\n<b>Количество предложений:</b> <code>{aos}</code>\n<b>Количество символов:</b> <code>{aoc}</code> (<code>{aocws}</code> без пробелов)'
    #     if image is not None:
    #         await message.answer_photo(BufferedInputFile(image.getvalue(), filename='image.png'), caption=answer_text,
    #                                    parse_mode=ParseMode.HTML)
    #     else:
    #         await message.answer(answer_text, parse_mode=ParseMode.HTML)

    else:
        async with aiohttp.ClientSession() as session:
            im = IndigoMath(session)
            aliases_dict = await sql.get_data(message.from_user.id, 'aliases')
            args = low.split(' ')
            # await message.answer(str(aliases))
            # await message.answer(str(args))
            if args[0] in aliases_dict:
                await bot.send_chat_action(message.chat.id, 'upload_photo')
                if len(args) > 2:
                    var = args[1]
                    vars_list = await nums_from_input(var)
                mgdz = ModernGDZ(message.from_user.id)
                gdzput = mgdz.GdzPutinaFun()
                try:
                    destination_url = str(aliases_dict[args[0]])
                    task_groups = await gdzput.get_task_groups(destination_url)
                    if len(args) < 3:
                        err1 = f'<b>Неправильно введены аргументы!</b>\nПример: <code>{args[0]} {args[1] if len(args) > 1 else "100"}</code> <i>(номер задания)</i>'
                        err1 = err1 + ' <code>1</code> <i>(номер группы)</i>\n<b>Доступные номера групп:</b>\n' + f'\n'.join(
                            f'<b>{c + 1}</b>. <code>{d}: {" | ".join(list(task_groups[d].keys())[:4])}</code>...' for
                            c, d
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
            elif 'ai' in low:
                await cancel_state(state)
                await ai_command(message=message, state=state,
                                 command=CommandObject(prefix='/', command='ai', mention=None))
                await message.delete()
            elif 'wolfram' in low:
                # await cancel_state(state)
                await wolfram_command(message=message, state=state)
            elif 'uchus.online' in low:
                # await cancel_state(state)
                await uchus_command(message, state)
            elif 'орфоэпия' in low:
                await orthoepy(message, state)
            elif 'закончить' in low or 'отмена' in low:
                await message.delete()
                await cancel_state(state)
                await main_message(message)
            else:
                loading_msg = await message.answer(
                    f"<i>Поиск формул по запросу </i>'<code>{html.quote(message.text)}</code>'...",
                    disable_notification=True)
                await bot.send_chat_action(message.chat.id, 'typing')
                await message.delete()
                formulas = await im.formulas_searcher(low)
                if len(formulas) == 0:
                    await message.answer(
                        f'<b>Не найдено никаких формул по запросу:</b> <code>{html.quote(message.text)}</code>')
                else:
                    lines = [f'<a href="{formulas[f][2]}">{f}</a>' for f in formulas]
                    chunks = [lines[i:i + 70] for i in range(0, len(lines), 70)]
                    for chunk in chunks:
                        await message.answer(
                            f'<b>Формулы по запросу:</b> <i>{html.quote(message.text)}</i> <b>({len(formulas)})</b>\n' + '\n'.join(
                                chunk), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                await loading_msg.delete()


@dp.message(F.chat.type == 'group')
async def group(message: Message):
    await message.answer('hi group')


# @dp.message(IsAdmin())
# async def other_content_admin(message: Message):
#     cp = message.content_type
#     await message.answer(cp)
#     if cp == 'sticker':
#         await message.answer(hcode(message.sticker.file_id), parse_mode=ParseMode.HTML)
#     elif cp == 'photo':
#         await message.answer(hcode(message.photo[-1].file_id), parse_mode=ParseMode.HTML)
#     elif cp == 'audio':
#         await message.answer(hcode(message.audio.file_id), parse_mode=ParseMode.HTML)
#     elif cp == 'document':
#         await message.answer(hcode(message.document.file_id), parse_mode=ParseMode.HTML)
#     elif cp == 'video':
#         await message.answer(hcode(message.video.file_id), parse_mode=ParseMode.HTML)
#     elif cp == 'video_note':
#         await message.answer(hcode(message.video_note.file_id), parse_mode=ParseMode.HTML)
#     elif cp == 'voice':
#         await message.answer(hcode(message.voice.file_id), parse_mode=ParseMode.HTML)
#     else:
#         await message.answer('undefined content_type')


@dp.message()
async def other_content(message: Message, bot: Bot):
    # await message.answer('Я еще не настолько умный')
    cp = message.content_type
    if cp == 'photo':
        filet = message.photo[-1]
    elif cp == 'audio':
        filet = message.audio
    elif cp == 'document':
        filet = message.document
    elif cp == 'video':
        filet = message.video
    elif cp == 'video_note':
        filet = message.video_note
    elif cp == 'voice':
        filet = message.voice
    else:
        await message.answer('undefined content_type')
        return

    await bot.send_chat_action(message.chat.id, 'typing')
    file_size = filet.file_size / 1024 ** 2
    if file_size > 20:
        await message.answer('Невозможно загрузить файл размером больше 20 МБ')
        return
    file_size_text = f'{round(file_size, 2)} МБ' if file_size > 1 else f'{round(file_size * 1024, 2)} КБ'
    file = await bot.download(filet.file_id)
    file_info = await bot.get_file(filet.file_id)
    file_name = file_info.file_path.split('/')[-1]

    async with aiohttp.ClientSession() as session:
        direct_link = await get_file_direct_link(file, session, file_name)
    await message.answer(
        f'<b>Прямая ссылка: </b> {html.quote(direct_link)}\n<b>Размер файла: </b><code>{file_size_text}</code>',
        parse_mode=ParseMode.HTML)


@dp.callback_query()
async def callback(call: CallbackQuery, state: FSMContext):
    if call.data == 'cancel':
        await cancel_state(state)
        # await call.message.answer('Действие отменено.')
        await cancel(call.message, state)
    elif call.data.startswith('uchus_'):
        param = call.data.replace('uchus_', '')
        settings = await sql.get_uchus_settings(call.from_user.id)

        async with aiohttp.ClientSession() as session:
            uo = UchusOnline(session, uchus_cookies)
            topics = await uo.get_banks_id()
            target_topic = [topic for topic in topics if param in topic][0]
            tasks = await uo.get_tasks(topics[target_topic],
                                       search_type='complexity_asc' if settings.complexity_asc else 'complexity_desc',
                                       min_complexity=settings.min_complexity, max_complexity=settings.max_complexity,
                                       pages=2)
        if len(tasks) > 0:
            markup = InlineKeyboardBuilder()
            completed_tasks = await sql.get_data(call.from_user.id, 'done', 'uchus_online')
            for task_id, task in tasks.items():
                addition = ''
                if task_id in completed_tasks:
                    addition = ' ✅'
                markup.row(InlineKeyboardButton(text=f'{task_id}, {task.difficulty}% {addition}',
                                                callback_data=f'uchust_{task_id}'))
            await call.message.answer('<b>Задания:</b>', reply_markup=markup.as_markup())
        else:
            await call.message.answer('<b>Не найдено ни одного задания! Проверьте ваши настройки.</b>')

    elif call.data.startswith('uchust_'):
        param = call.data.replace('uchust_', '')
        async with aiohttp.ClientSession() as session:
            uo = UchusOnline(session, uchus_cookies)
            task = await uo.get_task(int(param))

            img_from_text = (await image_from_text(task.content)).getvalue()
            if task.img is not None:
                async with session.get(task.img) as response:
                    image = (await image_gluer(img_from_text, (await response.read(), True))).getvalue()
            else:
                image = img_from_text
        await state.set_state(UchusOnlineState.ans)
        await state.update_data({'task': task})
        await call.message.answer_photo(BufferedInputFile(image, 'photo.png'), reply_markup=await reply_cancel_markup())

    elif call.data.startswith('uchuss_'):
        current_settings = await sql.get_uchus_settings(call.from_user.id)
        param = call.data.replace('uchuss_', '')
        if param == 'complexity':
            # await sql.change_data_type(call.from_user.id, 'complexity_asc', not (current_settings.complexity_asc), 'uchus_online')
            await sql.update_data(call.from_user.id, 'complexity_asc', not current_settings.complexity_asc,
                                  'uchus_online')
            await call.message.edit_reply_markup(reply_markup=await uchus_online_settings_markup(call.from_user.id))
        elif param == 'diff':
            mtr = await call.message.answer(
                'Напишите диапазон <b>через пробел</b>\n<i>Например: </i><code>80 90</code> = <code>от 80% до 90%</code>')
            await state.update_data({'msg_to_edit': call.message, 'msg_to_remove': mtr})
            await state.set_state(UchusOnlineState.change_diff)

    elif call.data.startswith('alias_del'):
        param = call.data.replace('alias_del-', '')

        old_data = dict(await sql.get_data(call.from_user.id, 'aliases'))
        old_data.pop(param)

        # await sql.change_data_jsonb(call.from_user.id, 'aliases', old_data)
        await sql.update_data(call.from_user.id, 'aliases', old_data)
        await call.answer(f'Alias \'{param}\' успешно удален!')

        al_text = await command_alias(call.from_user.id)
        await call.message.edit_text(f'<b>Список alias\'ов:\nНажать для удаления.</b>\n{al_text[0]}',
                                     reply_markup=al_text[1].as_markup(), disable_web_page_preview=True)
    elif call.data.startswith('docs_'):
        param = call.data.replace('docs_', '')

        await call.message.answer_document(constants.doc_ids[param])

    elif call.data.startswith(tuple(['2', '3', '4', '5'])):
        call.message.text = call.data
        await average_mark(message=call.message, state=state)

    elif call.data.startswith('encryption_'):
        await cancel_state(state)
        if call.data == 'encryption_encrypt':
            msg = await call.message.answer('<b>Введите текст для зашифровки: </b>', reply_markup=await reply_cancel_markup())
            await state.set_state(EncryptionState.encrypt_st)
        else:
            msg = await call.message.answer('<b>Введите шифр для расшифровки: </b>', reply_markup=await reply_cancel_markup())
            await state.set_state(EncryptionState.decrypt_st)
        await state.update_data({'delete_this_msgs': [msg]})
    await call.answer()


async def main():
    bot = Bot(token, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)


if __name__ == '__main__':
    # nltk.download('punkt', print_error_to=TextIO())
    # nltk.download('stopwords', print_error_to=TextIO())
    logger.success('Telegram bot has started!')
    asyncio.run(main())
