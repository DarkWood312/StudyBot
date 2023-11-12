import _io
import io
import string
import typing

from aiogram import html
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.media_group import MediaGroupBuilder
from nltk import word_tokenize, sent_tokenize
from pymorphy3 import MorphAnalyzer
from emoji import emojize

from random import shuffle

from nltk.corpus import stopwords
from wordcloud import WordCloud

import db
from config import sql
from exceptions import NumDontExistError, BaseDontExistError
from keyboards import menu_markup


async def remove_chars_from_text(text, chars) -> str:
    return "".join([ch for ch in text if ch not in chars])


async def text_analysis(text: str, user_id: int=None, count_digits: bool = False, convert_to_image: bool = True) -> typing.Dict[str, int | io.BytesIO]:
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
    return {'amount_of_words': len(wordt), 'amount_of_sentences': len(sentencet), 'amount_of_chars': len(text.lower()), 'amount_of_chars_without_space': len(text.lower().replace(' ', '')), 'image': bio}

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


async def cancel_state(state: FSMContext):
    state_ = await state.get_state()
    if state_ is not None:
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