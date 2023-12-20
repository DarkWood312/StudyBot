import base64
import builtins

import aiohttp
from aiogram import Bot, html
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BufferedInputFile

from config import futureforge_api, token
from defs import cancel_state
from keyboards import menu_markup


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
    imgur_file_url = ''
    if message.content_type in ('photo', 'document'):
        file_id = ''
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
        elif message.content_type == 'document':
            file_id = message.document.file_id
        get_path = f'https://api.telegram.org/bot{token}/getFile?file_id={file_id}'

        async with session.get(get_path) as response:
            file_path = (await response.json())['result']['file_path']
        file_url = f'https://api.telegram.org/file/bot{token}/{file_path}'

        async with session.get(file_url) as response:
            bytes_file = await response.read()

        async with session.post('https://api.imgur.com/3/upload', data={'image': bytes_file}) as response:
            imgur_file_url = (await response.json())['data']['link']

    try:
        if 'chatCode' not in data:
            resp, new_chatcode = await ai_method(text + f' {imgur_file_url}')
            await state.update_data({'chatCode': new_chatcode})
        else:
            resp = (await ai_method(text + f' {imgur_file_url}', data['chatCode']))[0]
        try:
            await message.answer(f'*{ai_name}💬:* {resp}', parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await message.answer(f'<b>{ai_name}💬:</b> {html.quote(resp)}', parse_mode=ParseMode.HTML)
    except aiohttp.ContentTypeError as e:
        await message.answer(e.message)


async def image_ai_tg(message: Message, state: FSMContext, bot: Bot, ai_method, ai_name: str):
    if not await ai_func_start(message, state, bot, 'upload_photo'):
        await cancel(message, state)
        return
    try:
        img = await ai_method(message.text, ' ')
        await message.answer_photo(BufferedInputFile(bytes(img), message.text),
                                   caption=f'<b>{ai_name}🦋:</b> <code>{html.quote(message.text)}</code>\n@{(await bot.get_me()).username}')
    except Exception as e:
        print(e)
        await message.answer(html.quote(str(e)))


async def cancel(message: Message, state: FSMContext):
    await cancel_state(state)
    await message.answer('Возврат в меню.', reply_markup=await menu_markup(message.from_user.id))
    await message.delete()


class AI:
    def __init__(self, session: aiohttp.client.ClientSession):
        self.session = session
        self.headers = {'apikey': futureforge_api, 'Content-Type': 'application/json', 'Accept': 'application/json'}

    async def chatgpt_turbo(self, message: str, chatcode: str = None) -> tuple[str, str]:
        if chatcode is None:
            async with self.session.post('https://api.futureforge.dev/chatgpt-turbo/create',
                                         json={'message': message}, headers=self.headers) as r:
                out = await r.json()
        else:
            async with self.session.post('https://api.futureforge.dev/chatgpt-turbo/chat',
                                         json={'message': message, 'chatCode': chatcode}, headers=self.headers) as r:
                out = await r.json()

        return out['message'], out['chatCode']

    async def gemini_pro(self, message: str, chatcode: str = None) -> tuple[str, str]:
        if chatcode is None:
            async with self.session.post('https://api.futureforge.dev/gemini_pro/create',
                                         json={'message': message}, headers=self.headers) as r:
                out = await r.json()
        else:
            async with self.session.post('https://api.futureforge.dev/gemini_pro/chat',
                                         json={'message': message, 'chatCode': chatcode}, headers=self.headers) as r:
                out = await r.json()

        return out['message'], out['chatCode']

    async def midjourney_v4(self, prompt: str, convert_to_bytes: bool = False) -> str | bytes:
        async with self.session.post('https://api.futureforge.dev/image/openjourneyv4', params={'text': prompt},
                                     headers=self.headers) as r:
            img = (await r.json())['image_base64']
            if convert_to_bytes:
                img = base64.b64decode(img)
            return img

    async def playgroundv2(self, prompt: str, negative_prompt: str = ' ',
                           convert_to_bytes: bool = False) -> str | bytes:
        async with self.session.post('https://api.futureforge.dev/image/playgroundv2',
                                     params={'prompt': prompt, 'negative_prompt': negative_prompt},
                                     headers=self.headers) as r:
            img = (await r.json())['image_base64']
            if convert_to_bytes:
                img = base64.b64decode(img)
            return img

    async def stable_diffusion_xl_turbo(self, prompt: str, convert_to_bytes: bool = False) -> str | bytes:
        async with self.session.post('https://api.futureforge.dev/image/sdxl-turbo',
                                     params={'text': prompt},
                                     headers=self.headers) as r:
            img = (await r.json())['image_base64']
            if convert_to_bytes:
                img = base64.b64decode(img)
            return img

    async def claude(self, message: str, chatcode: str = None) -> tuple[str, str]:
        if chatcode is None:
            async with self.session.post('https://api.futureforge.dev/claude-instant/create',
                                         json={'message': message}, headers=self.headers) as r:
                out = await r.json()
        else:
            async with self.session.post('https://api.futureforge.dev/claude-instant/chat',
                                         json={'message': message, 'chatCode': chatcode}, headers=self.headers) as r:
                out = await r.json()

        return out['message'], out['chatCode']
