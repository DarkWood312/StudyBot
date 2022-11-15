import logging
from aiogram import Bot, Dispatcher, executor, types
from gdz import GDZ
import db
from config import token, sql

logging.basicConfig(level=logging.DEBUG)
bot = Bot(token=token)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    sql.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)
    await message.answer(db.gdz_help, parse_mode=types.ParseMode.MARKDOWN)


@dp.message_handler()
async def other_messages(message: types.Message):
    sql.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name,
                 message.from_user.last_name)
    low = message.text.lower()
    # *  gdz...
    if ('алг' in low) or ('alg' in low):
        subject, num = low.split(' ', 1)
        num = int(num)
        response = await GDZ.algeu(num, doc=True if subject[-1].strip() in ['к', 'k'] else False)
        for group in response:
            await message.answer_media_group(group)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
