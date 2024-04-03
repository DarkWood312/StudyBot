import io
import itertools
import logging
import string
import sys
import textwrap
import typing

import aiohttp
from PIL import Image
from aiogram import html
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bs4 import BeautifulSoup
from matplotlib import pyplot as plt
# from nltk import word_tokenize, sent_tokenize
from pymorphy3 import MorphAnalyzer

# from nltk.corpus import stopwords
# from wordcloud import WordCloud

import extra.constants as constants
from extra.config import sql
from extra.exceptions import NumDontExistError, BaseDontExistError, WolframException
from extra.keyboards import menu_markup


async def remove_chars_from_text(text, chars) -> str:
    return "".join([ch for ch in text if ch not in chars])


# ! Deprecated
# async def text_analysis(text: str, user_id: int = None, count_digits: bool = False, convert_to_image: bool = True) -> \
#         typing.Dict[str, int | io.BytesIO]:
#     # nltk.download('punkt')
#     # nltk.download('stopwords')
#
#     text = text.strip()
#
#     spec_chars = string.punctuation + '\n\xa0«»\t—…'
#     if not count_digits:
#         spec_chars = spec_chars + string.digits
#     stopw = stopwords.words('russian')
#     bio = None
#     if convert_to_image:
#         wc_user_settings = await sql.get_wordcloud_settings(user_id=user_id)
#         m = MorphAnalyzer(lang='ru')
#         words = ' '.join([m.normal_forms(i)[0] for i in text.split(' ')])
#         wc = WordCloud(**wc_user_settings, stopwords=stopw).generate(text=words)
#         bio = io.BytesIO()
#         bio.name = 'image.png'
#         wc.to_image().save(bio, 'PNG')
#         bio.seek(0)
#
#     text_no_punctuation = ((await remove_chars_from_text(text.lower(), spec_chars))
#                            .replace(' - ', ' ').replace(' – ', ' ').replace(' — ', ' '))
#     wordt = word_tokenize(text_no_punctuation, language='russian')
#     sentencet = sent_tokenize(text, language='russian')
#     return {'amount_of_words': len(wordt), 'amount_of_sentences': len(sentencet), 'amount_of_chars': len(text.lower()),
#             'amount_of_chars_without_space': len(text.lower().replace(' ', '')), 'image': bio}


async def orthoepy_word_formatting(words: list, pos: int, amount_of_words: int | None = None):
    """
    PARSEMODE.HTML !!!
    """
    if amount_of_words is None:
        amount_of_words = len(words)
    word = ''
    for letter in words[pos]:
        if letter.lower() in constants.gl:
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
    await message.answer(constants.main_message, parse_mode=ParseMode.HTML,
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


async def get_file_direct_link(file: typing.BinaryIO, session: aiohttp.client.ClientSession, filename: str = None,
                               expires_in: str | None = None) -> str:
    form_data = aiohttp.FormData()
    form_data.add_field('reqtype', 'fileupload')
    base_url = 'https://catbox.moe/user/api.php'
    fileb = file.read()
    file_size = sys.getsizeof(file.read())
    if expires_in or ((file_size / 1024 ** 2) > 200):
        base_url = 'https://litterbox.catbox.moe/resources/internals/api.php'
        form_data.add_field('time', expires_in)
    form_data.add_field('fileToUpload', fileb, filename=filename if filename else file.name)
    async with session.post(base_url, data=form_data, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.771 YaBrowser/23.11.2.771 Yowser/2.5 Safari/537.36'}) as r:
        # if not r.status == 200:
        #     await get_file_direct_link(file, session, filename, expires_in='72h')
        # else:
        return await r.text()


async def wolfram_getimg(api: str, query: str, return_: typing.Literal['url', 'bytes', 'image'] = 'url', **params) -> \
        tuple[dict, bytes | None]:
    """
    :param api: wolfram_api
    :param query: request query
    :param return_: url | bytes | image
    :param params: more parameters if needed
    :return: (dict of images, Image | None)
    """
    images = {}
    params.update({'appid': api, 'input': query, 'format': 'image', 'output': 'json'})
    async with aiohttp.ClientSession() as session:
        async with session.get('http://api.wolframalpha.com/v2/query', params=params) as r:
            if r.status != 200:
                raise WolframException.StatusNot200(await r.text())
            rjs = await r.json()
            if not (rjs['queryresult']['success']):
                raise WolframException.NotSuccess
            logging.debug(f'WOLFRAMALPHA: {rjs}')
        for i in rjs['queryresult']['pods']:
            for s in i['subpods']:
                img_src = s['img']['src']
                if return_ == 'bytes' or return_ == 'image':
                    async with session.get(img_src) as r:
                        images[await r.read()] = s['img']['alt']
                else:
                    images[img_src] = s['img']['alt']

    iobuf = None
    if return_ == 'image':
        iobuf = await image_gluer(*images)

    return images, iobuf.getvalue()


async def ege_points_converter(primitive_points: int,
                               subject: typing.Literal[*constants.subjects, 'all']) -> str | bool | dict[
    str, str | bool]:
    ege_points = constants.ege_points
    if subject == 'all':
        res = {}
        for s in constants.subjects:
            val = ege_points[primitive_points - 1][s]
            if val:
                res[s] = ege_points[primitive_points - 1][s]
    else:
        res = ege_points[primitive_points - 1][subject]
    return res


async def image_gluer(*images: tuple[bytes, bool] | bytes) -> io.BytesIO:
    images = [(i, False) if not (isinstance(i, tuple)) else i for i in images]
    imgs = [(Image.open(io.BytesIO(i[0])), i[1]) for i in images]
    overall_size = list(zip(*[i[0].size for i in imgs]))
    size = tuple([max(overall_size[0]) + 10, sum(overall_size[1]) + 10])
    ready_img = Image.new('RGBA', size, color='white')
    h = 5
    for i in imgs:
        ready_img.paste(i[0], (size[0] // 2 if i[1] else 5, h))
        h += i[0].height

    iobuf = io.BytesIO()
    ready_img.save(iobuf, 'png')
    return iobuf


async def init_user(message: Message):
    await sql.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name,
                       message.from_user.last_name)
    await sql.add_wordcloud_user(user_id=message.from_user.id)
    await sql.add_uchus_user(user_id=message.from_user.id)


async def image_from_text(s) -> io.BytesIO:
    texts = textwrap.wrap(s, 50)
    fig = plt.figure(dpi=300, figsize=(5, 0.4 * len(texts)))

    plt.axis('off')
    plt.text(0.5, 0.5, '\n'.join(texts), size=8, ha='center', va='center')
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')

    return buffer


class IndigoMath:

    def __init__(self, session: aiohttp.client.ClientSession):
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
