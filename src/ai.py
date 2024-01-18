import base64
import logging

import aiohttp
from aiogram import Bot, html
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BufferedInputFile
from googletrans import Translator

from config import futureforge_api
from defs import cancel_state, get_file_direct_link
from keyboards import menu_markup
from exceptions import *


async def ai_func_start(message: Message, state: FSMContext, bot: Bot, action: str = 'typing'):
    if message.text is not None and 'Закончить разговор❌' in message.text:
        return False
    await bot.send_chat_action(message.chat.id, action)
    return True


async def msg_ai_tg(message: Message, state: FSMContext, bot: Bot, ai_method, ai_name: str,
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
        logging.info(f'created image with link --> {file_direct_link}')

    try:
        if 'chatCode' not in data:
            resp, new_chatcode = await ai_method(text + f' {file_direct_link}')
            await state.update_data({'chatCode': new_chatcode})
        else:
            resp = (await ai_method(text + f' {file_direct_link}', data['chatCode']))[0]
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
    except aiohttp.ContentTypeError as e:
        await message.answer(html.quote(e.message))
    # except Exception as e:
    #     await message.answer(f'{e} error')


async def image_ai_tg(message: Message, state: FSMContext, bot: Bot, ai_method, ai_name: str):
    if not await ai_func_start(message, state, bot, 'upload_photo'):
        await cancel(message, state)
        return
    try:
        text = message.text
        translator = Translator()
        source_lang = translator.detect(text).lang
        if source_lang != 'en':
            text = translator.translate(text, 'en', source_lang).text
        img = await ai_method(text, convert_to_bytes=True)
        file = BufferedInputFile(img, message.text)
        caption = f'<b>{ai_name}🦋:</b> <code>{html.quote(message.text)}</code>\n@{(await bot.get_me()).username}'
        await message.answer_photo(file, caption=caption)
        # await message.answer_document(file, caption=caption, disable_notification=True)
    except AIException.TooManyRequests as e:
        await message.answer(e.message)
    except Exception as e:
        await message.answer(f'{e} error')


async def cancel(message: Message, state: FSMContext):
    await cancel_state(state)
    await message.answer('Возврат в меню.', reply_markup=await menu_markup(message.from_user.id))
    await message.delete()


class AI:
    def __init__(self, session: aiohttp.client.ClientSession):
        self.session = session
        self.headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        self.request_params = {'headers': self.headers, 'params': {'apikey': futureforge_api}, 'json': {'model': 'string'}}

    async def chatgpt_turbo(self, message: str, chatcode: str = None) -> tuple[str, str]:
        self.request_params['json']['message'] = message
        if chatcode is None:
            async with self.session.post('https://api.futureforge.dev/chatgpt-turbo/create', **self.request_params) as r:
                out = await r.json()
        else:
            self.request_params['json']['chatCode'] = chatcode
            async with self.session.post('https://api.futureforge.dev/chatgpt-turbo/chat', **self.request_params) as r:
                out = await r.json()

        if r.status == 429:
            raise AIException.TooManyRequests()
        return out['message'], out['chatCode']

    async def gemini_pro(self, message: str, chatcode: str = None) -> tuple[str, str]:
        self.request_params['json']['message'] = message
        if chatcode is None:
            async with self.session.post('https://api.futureforge.dev/gemini_pro/create', **self.request_params) as r:
                out = await r.json()
        else:
            self.request_params['json']['chatCode'] = chatcode
            async with self.session.post('https://api.futureforge.dev/gemini_pro/chat', **self.request_params) as r:
                out = await r.json()
        if r.status == 429:
            raise AIException.TooManyRequests()
        return out['message'], out['chatCode']

    async def midjourney_v4(self, prompt: str, convert_to_bytes: bool = False) -> str | bytes:
        self.request_params['params']['text'] = prompt
        async with self.session.post('https://api.futureforge.dev/image/openjourneyv4', **self.request_params) as r:
            if r.status == 429:
                raise AIException.TooManyRequests()
            img = (await r.json())['image_base64']
            if convert_to_bytes:
                img = base64.b64decode(img)
            return img

    async def playgroundv2(self, prompt: str, negative_prompt: str = ' ',
                           convert_to_bytes: bool = False) -> str | bytes:
        self.request_params['params']['prompt'] = prompt
        self.request_params['params']['negative_prompt'] = negative_prompt
        async with self.session.post('https://api.futureforge.dev/image/playgroundv2', **self.request_params) as r:
            if r.status == 429:
                raise AIException.TooManyRequests()
            img = (await r.json())['image_base64']
            if convert_to_bytes:
                img = base64.b64decode(img)
            return img

    async def stable_diffusion_xl_turbo(self, prompt: str, convert_to_bytes: bool = False) -> str | bytes:
        self.request_params['params']['text'] = prompt
        async with self.session.post('https://api.futureforge.dev/image/sdxl-turbo', **self.request_params) as r:
            if r.status == 429:
                raise AIException.TooManyRequests()
            img = (await r.json())['image_base64']
            if convert_to_bytes:
                img = base64.b64decode(img)
            return img

    async def claude(self, message: str, chatcode: str = None) -> tuple[str, str]:
        self.request_params['json']['message'] = message
        if chatcode is None:
            async with self.session.post('https://api.futureforge.dev/claude-instant/create', **self.request_params) as r:
                out = await r.json()
        else:
            self.request_params['json']['chatCode'] = chatcode
            async with self.session.post('https://api.futureforge.dev/claude-instant/chat', **self.request_params) as r:
                out = await r.json()
        if r.status == 429:
            raise AIException.TooManyRequests()
        return out['message'], out['chatCode']

    async def mistral_medium(self, message: str, chatcode: str = None) -> tuple[str, str]:
        self.request_params['json']['message'] = message
        if chatcode is None:
            async with self.session.post('https://api.futureforge.dev/mistral_medium/create', **self.request_params) as r:
                out = await r.json()
        else:
            self.request_params['json']['chatCode'] = chatcode
            async with self.session.post('https://api.futureforge.dev/mistral_medium/chat', **self.request_params) as r:
                out = await r.json()
        if r.status == 429:
            raise AIException.TooManyRequests()
        return out['message'], out['chatCode']

    async def dalle3(self, prompt: str, convert_to_bytes: bool = False) -> str | bytes:
        async with self.session.post('https://api.futureforge.dev/image/dalle3',
                                     json={'prompt': prompt},
                                     headers=self.headers, params={'apikey': futureforge_api}) as r:
            if r.status == 429:
                raise AIException.TooManyRequests()
            img = (await r.json())['image_base64']
            if convert_to_bytes:
                img = base64.b64decode(img)
            return img

    async def stable_diffusion_video(self, image_url: str, num_videos: int = 1):
        async with self.session.post('https://api.futureforge.dev/svd', params={k: v for k, v in locals().items() if k != 'self'}) as r:
            if r.status == 429:
                raise AIException.TooManyRequests()
            vid = (await r.json())['']
