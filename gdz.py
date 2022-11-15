import requests
from bs4 import BeautifulSoup
from aiogram import types

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 '
                  'Safari/537.36 ',
    'referer': 'https://gdz.ru/class-10/algebra/alimov-15/'
}


async def process(arr: list, sep: int = 10):
    l = [types.InputMediaPhoto(i) for i in arr]
    return [l[i:i + sep] for i in range(0, len(l), sep)]

class GDZ:


    async def algru(num: int):
        imgs = []
        r = requests.get(f'https://gdz.ru/class-10/algebra/alimov-15/{num}-nom/', headers=headers)
        raw_imgs = BeautifulSoup(r.content, 'lxml').find_all(class_='with-overtask')
        for img in raw_imgs:
            imgs.append('https:' + img.find('img')['src'])
        return await process(imgs)
