import requests
from bs4 import BeautifulSoup
from aiogram import types

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 '
                  'Safari/537.36 ',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
}


async def process(arr: list, doc: bool = False, sep: int = 10):
    if doc:
        l = [types.InputMediaDocument(i) for i in arr]
    else:
        l = [types.InputMediaPhoto(i) for i in arr]
    return [l[i:i + sep] for i in range(0, len(l), sep)]


class GDZ:

    async def algeu(num: int, doc: bool = False):
        imgs = []
        r = requests.get(
            f'https://www.euroki.org/gdz/ru/algebra/10_klass/reshebnik-po-algebre-10-klasss-alimov-502/zadanie-{num}',
            headers=headers)
        imgs_block = BeautifulSoup(r.content, 'lxml').find_all(class_='gdz_image')
        for img in imgs_block:
            imgs.append(img['src'])
        return await process(imgs, doc=doc)
