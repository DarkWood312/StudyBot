import requests
from bs4 import BeautifulSoup
from aiogram import types

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 '
                  'Safari/537.36 ',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'referer': 'https://gdz.ru/class-10/algebra/alimov-15/',
    'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
    'authority': 'gdz.ru'
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
        return [r.status_code, r.content][0]
        # return await process(imgs)
