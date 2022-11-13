import logging
from aiogram import Bot, Dispatcher, executor, types
from gdz import GDZ
import db

API_TOKEN = '5681353642:AAHQ-tjhwjU0yX7rrZWS2BHqXWhrcAS4jww'
logging.basicConfig(level=logging.DEBUG)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    await message.answer(db.gdz_help, parse_mode=types.ParseMode.MARKDOWN)


@dp.message_handler()
async def other_messages(message: types.Message):
    low = message.text.lower()
    # *  gdz...
    # try:
    if ('алг ' in low) or ('alg' in low):
        num = int(low.split(' ')[1])
        for mediagroup in await GDZ.algru(num):
            await message.answer_media_group(mediagroup)
    # except ValueError:
    #     await message.answer('Неправильно введен номер задания')
    #     await message.answer(db.gdz_help, parse_mode=types.ParseMode.MARKDOWN)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
