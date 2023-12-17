import base64
import io
import itertools
import string
import typing

import aiogram
import aiohttp
import requests
from aiogram import html, Bot
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.media_group import MediaGroupBuilder
from bs4 import BeautifulSoup
from nltk import word_tokenize, sent_tokenize
from pymorphy3 import MorphAnalyzer
from emoji import emojize

from random import shuffle

from nltk.corpus import stopwords
from wordcloud import WordCloud

import db
from config import sql, proxy
from exceptions import NumDontExistError, BaseDontExistError
from keyboards import menu_markup


async def remove_chars_from_text(text, chars) -> str:
    return "".join([ch for ch in text if ch not in chars])


async def text_analysis(text: str, user_id: int = None, count_digits: bool = False, convert_to_image: bool = True) -> \
        typing.Dict[str, int | io.BytesIO]:
    # nltk.download('punkt')
    # nltk.download('stopwords')

    text = text.strip()

    spec_chars = string.punctuation + '\n\xa0«»\t—…'
    if not count_digits:
        spec_chars = spec_chars + string.digits
    stopw = stopwords.words('russian')
    bio = None
    if convert_to_image:
        wc_user_settings = await sql.get_wordcloud_settings(user_id=user_id)
        m = MorphAnalyzer(lang='ru')
        words = ' '.join([m.normal_forms(i)[0] for i in text.split(' ')])
        wc = WordCloud(**wc_user_settings, stopwords=stopw).generate(text=words)
        bio = io.BytesIO()
        bio.name = 'image.png'
        wc.to_image().save(bio, 'PNG')
        bio.seek(0)

    text_no_punctuation = ((await remove_chars_from_text(text.lower(), spec_chars))
                           .replace(' - ', ' ').replace(' – ', ' ').replace(' — ', ' '))
    wordt = word_tokenize(text_no_punctuation, language='russian')
    sentencet = sent_tokenize(text, language='russian')
    return {'amount_of_words': len(wordt), 'amount_of_sentences': len(sentencet), 'amount_of_chars': len(text.lower()),
            'amount_of_chars_without_space': len(text.lower().replace(' ', '')), 'image': bio}


async def orthoepy_word_formatting(words: list, pos: int, amount_of_words: int | None = None):
    """
    PARSEMODE.HTML !!!
    """
    if amount_of_words is None:
        amount_of_words = len(words)
    word = ''
    for letter in words[pos]:
        if letter.lower() in db.gl:
            letter = f'<b>{letter}</b>'
        word = word + letter
    output = f'<code>{pos + 1}/{amount_of_words})</code> {word.upper()}'
    return output


async def command_alias(user_id):
    aliases_dict = await sql.get_data(user_id, 'aliases')
    markup = InlineKeyboardBuilder()
    markup.add(*[InlineKeyboardButton(text=b, callback_data=f'alias_del-{b}') for b in aliases_dict.keys()])
    markup.adjust(3)

    aliases_text = ', '.join(
        f'<a href="{html.quote(aliases_dict[i])}">{html.quote(i)}</a>' for i in aliases_dict.keys())

    return aliases_text, markup


async def cancel_state(state: FSMContext, delete: bool = True):
    state_ = await state.get_state()
    if state_ is not None:
        if delete:
            data = await state.get_data()
            if 'delete_this_msgs' in data:
                for msg in data['delete_this_msgs']:
                    await msg.delete()
        await state.clear()


async def main_message(message: Message):
    await message.answer(db.main_message, parse_mode=ParseMode.HTML,
                         reply_markup=await menu_markup(message.from_user.id))


async def num_base_converter(num: int | str, to_base: int, from_base: int = 10):
    if (to_base or from_base) > 36:
        raise BaseDontExistError
    alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    if isinstance(num, str):
        try:
            n = int(num, from_base)
        except ValueError as e:
            raise NumDontExistError(f"Value '{num}' dont exist in '{from_base}' base", num, from_base)
    else:
        n = int(num)
        max_n = max([int(i) for i in str(n)])
        if max_n >= from_base:
            raise NumDontExistError(f"Value '{max_n}' dont exist in '{from_base}' base", max_n, from_base)
    if str(n).isdigit():
        n = int(n)
        if n < to_base:
            return alphabet[n]
        else:
            return (await num_base_converter(n // to_base, to_base)) + alphabet[n % to_base]


async def nums_from_input(inp: str) -> typing.List[str | int]:
    nums = [n.split('-') for n in inp.split(',')]
    numss = [range(int(n[0]), int(n[1]) + 1) for n in nums if len(n) > 1]
    numss = [[*n] for n in numss]
    nums = [n[0] for n in nums if len(n) == 1]
    ready = [*itertools.chain(nums, *numss)]
    ready = sorted([*map(int, [n for n in ready])]) if len(numss) > 0 else ready
    return ready


class IndigoMath:
    def __init__(self, session: aiohttp.client.ClientSession, proxy: str = proxy):
        self.session = session
        self.proxy = proxy

    async def formulas_groups(self) -> typing.Dict[str, typing.Dict[str, str]]:
        async with self.session.get('https://www.indigomath.ru/', proxy=self.proxy) as r:
            soup = BeautifulSoup(await r.text(), 'lxml').find_all(id='myTabContent')
            main_groups = {i.find_previous(class_='nav-link active').get_text(): i.find_all(class_='nav flex-column')
                           for i in soup}
            formula_groups = {}
            for k, v in main_groups.items():
                group = {}
                for g in v:
                    for i in g.find_all(class_='nav-link'):
                        group[i.get_text()] = 'https://indigomath.ru' + i.get('href')
                formula_groups[k] = group

        return formula_groups

    async def get_formulas(self, urls: str | list[str]) -> typing.Dict[str, typing.List[str]]:
        formulas = {}
        if isinstance(urls, str):
            urls = [urls]
        for url in urls:
            async with self.session.get(url, proxy=self.proxy) as fres:
                formulas_content = [f.find('a') for f in
                                    BeautifulSoup(await fres.text(), 'lxml').find_all(class_='s_formula_row')]
                for f in formulas_content:
                    formulas[f.find('img').get('alt').replace('saknis', '√').replace('\r', '')] = [
                        f.find_previous('a').getText(),
                        f.find('img').get('title').replace('\n',
                                                           ' | ').replace(
                            '\r', ''),
                        'https://www.indigomath.ru' + f.get('href')]

        return formulas

    async def formulas_searcher(self, query: str) -> typing.Dict[str, typing.List[str]]:
        url = f'https://www.indigomath.ru/poisk/?data%5Btags%5D={query}&data%5Bf_category%5D&page=1'

        async with self.session.get(url, proxy=self.proxy) as r:
            pages_content = BeautifulSoup(await r.text(), 'lxml').find('ul', class_='pagination')

            pages_to_parse = [url]
            if pages_content is not None:
                pages_to_parse = ['https://www.indigomath.ru' + e.get('href') for e in
                                  BeautifulSoup(await r.text(), 'lxml').find('ul', class_='pagination').find_all(
                                      class_='page-link')
                                  if
                                  e.getText().isdigit()]

            return await self.get_formulas(pages_to_parse)


async def ai_func_start(message: Message, state: FSMContext, bot: Bot, action: str = 'typing'):
    if 'Закончить разговор❌' in message.text:
        return False
    await bot.send_chat_action(message.from_user.id, action)
    return True


class AI:
    def __init__(self, session: aiohttp.client.ClientSession):
        self.session = session

    async def chatgpt_turbo(self, message: str, chatcode: str = None) -> tuple[str, str]:
        if chatcode is None:
            async with self.session.post('https://api.futureforge.dev/chatgpt-turbo/create',
                                         json={'message': message}) as r:
                out = await r.json()
        else:
            async with self.session.post('https://api.futureforge.dev/chatgpt-turbo/chat',
                                         json={'message': message, 'chatCode': chatcode}) as r:
                out = await r.json()

        return out['message'], out['chatCode']

    async def gemini_pro(self, message: str, chatcode: str = None) -> tuple[str, str]:
        if chatcode is None:
            async with self.session.post('https://api.futureforge.dev/gemini_pro/create',
                                         json={'message': message}) as r:
                out = await r.json()
        else:
            async with self.session.post('https://api.futureforge.dev/gemini_pro/chat',
                                         json={'message': message, 'chatCode': chatcode}) as r:
                out = await r.json()

        return out['message'], out['chatCode']

    async def midjourney_v4(self, prompt: str, convert_to_bytes: bool = False) -> str | bytes:
        async with self.session.post('https://api.futureforge.dev/image/openjourneyv4', params={'text': prompt}) as r:
            img = (await r.json())['image_base64']
            if convert_to_bytes:
                img = base64.b64decode(img)
            return img

    async def playgroundv2(self, prompt: str, negative_prompt: str = ' ',
                           convert_to_bytes: bool = False) -> str | bytes:
        async with self.session.post('https://api.futureforge.dev/image/playgroundv2',
                                     params={'prompt': prompt, 'negative_prompt': negative_prompt}) as r:
            img = (await r.json())['image_base64']
            if convert_to_bytes:
                img = base64.b64decode(img)
            return img
