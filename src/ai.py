import base64
import logging
import typing
from datetime import datetime

import aiohttp
from aiogram import Bot, html
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BufferedInputFile
from googletrans import Translator

from config import futureforge_api
from defs import cancel_state, get_file_direct_link
from keyboards import menu_markup
from exceptions import *

models = typing.Literal[
    "gpt-3-5",
    "gpt-3-5-turbo",
    "gpt-3-5-turbo-instruct",
    "claude-instant",
    "google-palm",
    "llama-2-7b",
    "llama-2-13b",
    "llama-2-70b",
    "code-llama-7b",
    "code-llama-13b",
    "code-llama-34b",
    "solar-0-70b",
    "gemini-pro",
    "mistral-medium"
]


async def ai_func_start(message: Message, state: FSMContext, bot: Bot, action: str = 'typing'):
    if message.text is not None and 'Закончить разговор❌' in message.text:
        return False
    await bot.send_chat_action(message.chat.id, action)
    return True


async def text2text(message: Message, state: FSMContext, bot: Bot, model: models, ai_name: str,
                    session: aiohttp.client.ClientSession):
    text = message.text or message.caption or ''

    if not await ai_func_start(message, state, bot, 'typing'):
        await cancel(message, state)
        return
    data = await state.get_data()
    file_direct_link = ''
    if message.content_type in ('photo', 'document'):

        file_tid = ''
        if message.content_type == 'photo':
            file_tid = message.photo[-1].file_id
        elif message.content_type == 'document':
            file_tid = message.document.file_id
        file = await bot.download(file_tid)
        file_name = (await bot.get_file(file_tid)).file_path.split('/')[-1]
        file_direct_link = await get_file_direct_link(file=file, session=session, filename=file_name, expires_in='1h')
        logging.debug(f'created image with link --> {file_direct_link}')

    try:
        if 'chatCode' not in data:
            resp, new_chatcode = await AI(session=session).chat(model, text + f' {file_direct_link}')
            await state.update_data({'chatCode': new_chatcode})
        else:
            resp = (await AI(session=session).chat(model, text + f' {file_direct_link}', data['chatCode']))[0]
        try:
            mresp = resp
            await message.answer(f'*{ai_name}💬:* {mresp}', parse_mode=ParseMode.MARKDOWN)
        except Exception:
            try:
                mresp = resp.replace('_', r'\_').replace('[', r'\[').replace(']', r'\]')
                await message.answer(f'*{ai_name}💬:* {mresp}', parse_mode=ParseMode.MARKDOWN)
            except Exception:
                await message.answer(f'<b>{ai_name}💬:</b> {html.quote(resp)}', parse_mode=ParseMode.HTML)
    except AIException.TooManyRequests as e:
        await message.answer(e.message)
    except AIException.ApiIsBroken as e:
        await message.answer(e.message)
    except aiohttp.ContentTypeError as e:
        await message.answer(html.quote(e.message))
    # except Exception as e:
    #     await message.answer(f'{e} error')


async def text2image(message: Message, state: FSMContext, bot: Bot, ai_method, ai_name: str, send_via_document: bool = False):
    if not await ai_func_start(message, state, bot, 'upload_photo'):
        await cancel(message, state)
        return
    try:
        text = message.text
        if '--doc' in text:
            send_via_document = True
            text = text.replace('--doc', '')
        translator = Translator()
        source_lang = translator.detect(text).lang
        if source_lang != 'en':
            text = translator.translate(text, 'en', source_lang).text
        img = await ai_method(text)
        file = BufferedInputFile(img, filename=f"{datetime.now().strftime('%d-%m--%H-%M-%S')}.jpg")
        caption = f'<b>{ai_name}🦋:</b> <code>{html.quote(message.text)}</code>\n@{(await bot.get_me()).username}'
        if send_via_document:
            await message.answer_document(file, caption=caption)
        else:
            await message.answer_photo(file, caption=caption)
        # await message.answer_document(file, caption=caption, disable_notification=True)
    except AIException.TooManyRequests as e:
        await message.answer(e.message)
    except Exception as e:
        await message.answer(f'{e} error')


async def image2image(message: Message, state: FSMContext, bot: Bot, ai_method, ai_name: str, send_via_document: bool = False):
    if not await ai_func_start(message, state, bot, 'upload_photo'):
        await cancel(message, state)
        return
    if len(message.photo) == 0 or message.caption == '':
        await message.answer('Отправьте фотографию с подписью!')
        return
    try:
        text = message.caption
        if '--doc' in text:
            send_via_document = True
            text = text.replace('--doc', '')
        photo = message.photo[-1]
        photob = await bot.download(photo.file_id)
        photo_name = (await bot.get_file(photo.file_id)).file_path.split('/')[-1]
        async with aiohttp.ClientSession() as session:
            photourl = await get_file_direct_link(photob, session, photo_name)
            img = await ai_method(photourl, text)
        params = (BufferedInputFile(img, filename=f"{datetime.now().strftime('%d-%m--%H-%M-%S')}.{photourl.split('.')[-1]}"), f'<b>{ai_name}🦋:</b> <code>{html.quote(text)}</code>\n@{(await bot.get_me()).username}')
        if send_via_document:
            await message.answer_document(params[0], caption=params[1])
        else:
            try:
                await message.answer_photo(params[0], caption=params[1])
            except TelegramBadRequest:
                await message.answer_document(params[0], caption=params[1])
    except AIException.TooManyRequests as e:
        await message.answer(e.message)


async def cancel(message: Message, state: FSMContext):
    await cancel_state(state)
    await message.answer('Возврат в меню.', reply_markup=await menu_markup(message.from_user.id))
    await message.delete()


class AI:
    def __init__(self, session: aiohttp.client.ClientSession):
        self.session = session
        self.headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        self.request_params = {'headers': self.headers, 'params': {'apikey': futureforge_api},
                               'json': {}}

    async def chat(self, model: models, message: str, chatcode: str = None):
        self.request_params['json']['message'] = message
        self.request_params['json']['model'] = model
        if chatcode is None:
            async with self.session.post('https://api.futureforge.dev/chat/create',
                                         **self.request_params) as r:
                out = await r.json()
        else:
            self.request_params['json']['chatCode'] = chatcode
            async with self.session.post('https://api.futureforge.dev/chat/chat', **self.request_params) as r:
                if r.status == 429:
                    raise AIException.TooManyRequests()
                out = await r.json()
        logging.debug(out)

        if not ('message' in out):
            raise AIException.ApiIsBroken()
        return out['message'], out['chatCode']

    async def midjourney_v4(self, prompt: str, convert_to_bytes: bool = False) -> bytes:
        self.request_params['params']['text'] = prompt
        async with self.session.post('https://api.futureforge.dev/image/openjourneyv4', **self.request_params) as r:
            if r.status == 429:
                raise AIException.TooManyRequests()
            out = await r.json()
        logging.debug(out)

        img = base64.b64decode(out['image_base64'])
        return img

    async def playgroundv2(self, prompt: str, negative_prompt: str = ' ') -> bytes:
        self.request_params['params']['prompt'] = prompt
        self.request_params['params']['negative_prompt'] = negative_prompt
        async with self.session.post('https://api.futureforge.dev/image/playgroundv2', **self.request_params) as r:
            if r.status == 429:
                raise AIException.TooManyRequests()
            out = await r.json()
        logging.debug(out)

        img = base64.b64decode(out['image_base64'])
        return img

    async def stable_diffusion_xl_turbo(self, prompt: str) -> bytes:
        self.request_params['params']['text'] = prompt
        async with self.session.post('https://api.futureforge.dev/image/sdxl-turbo', **self.request_params) as r:
            if r.status == 429:
                raise AIException.TooManyRequests()
            out = await r.json()
        logging.debug(out)

        img = base64.b64decode(out['image_base64'])
        return img

    # async def dalle3(self, prompt: str, convert_to_bytes: bool = False) -> str | bytes:
    #     async with self.session.post('https://api.futureforge.dev/image/dalle3',
    #                                  json={'prompt': prompt},
    #                                  headers=self.headers, params={'apikey': futureforge_api}) as r:
    #         if r.status == 429:
    #             raise AIException.TooManyRequests()
    #         img = (await r.json())['image_base64']
    #         if convert_to_bytes:
    #             img = base64.b64decode(img)
    #         return img

    async def stable_diffusion_video(self, image_url: str, num_videos: int = 1):
        async with self.session.post('https://api.futureforge.dev/svd',
                                     params={k: v for k, v in locals().items() if k != 'self'}) as r:
            if r.status == 429:
                raise AIException.TooManyRequests()
            vid = (await r.json())['']

    async def hcrt(self, image_url: str, prompt: str) -> bytes:
        self.request_params['params']['prompt'] = prompt
        self.request_params['params']['image_url'] = image_url
        async with self.session.post('https://api.futureforge.dev/image/hrct/', **self.request_params) as r:
            if r.status == 429:
                raise AIException.TooManyRequests()
            out = await r.json()
        logging.debug(out)

        async with self.session.get(out['image_url']) as r:
            img_bytes = await r.read()

        return img_bytes

    async def photomaker(self, image_url: str, prompt: str) -> bytes:
        self.request_params['params']['prompt'] = prompt
        self.request_params['params']['image_url'] = image_url
        async with self.session.post('https://api.futureforge.dev/image/photomaker/', **self.request_params) as r:
            if r.status == 429:
                raise AIException.TooManyRequests()
            out = await r.json()
        logging.debug(out)

        async with self.session.get(out['image_url']) as r:
            img_bytes = await r.read()

        return img_bytes
