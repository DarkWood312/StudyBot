import requests
from bs4 import BeautifulSoup
from aiogram import types
import db
from config import sql

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 '
                  'Safari/537.36 ',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
}


async def process(arr, doc: bool = False):
    if isinstance(arr, list):
        sep = 10
        if doc:
            l = [types.InputMediaDocument(i) for i in arr]
        else:
            l = [types.InputMediaPhoto(i) for i in arr]
    else:
        sep = 4096
        l = arr
    return [l[i:i + sep] for i in range(0, len(l), sep)]


class GDZ:

    def __init__(self, user_id):
        self.user_id = user_id

    async def init(self):
        self.status = bool(await sql.get_data(self.user_id, 'upscaled'))
        return self.status

    async def alg_euroki(self, num: int):
        link = f'https://www.euroki.org/gdz/ru/algebra/10_klass/reshebnik-po-algebre-10-klasss-alimov-502/zadanie-{num}'
        r = requests.get(link, headers=headers)
        if r.status_code != 200:
            raise ConnectionError
        imgs_block = BeautifulSoup(r.content, 'lxml').find_all(class_='gdz_image')
        imgs = [i['src'] for i in imgs_block]
        return [await process(imgs, await GDZ(self.user_id).init()), link]

    async def algm_pomogalka(self, paragraph: int, num: int):
        link = f'https://pomogalka.me/img/10-11-klass-mordkovich/{paragraph}-{num}.png'
        return [await process([link], await GDZ(self.user_id).init()), link]

    async def geom_megaresheba(self, num: int):
        link = f'https://megaresheba.ru/publ/reshebnik/geometrija/10_11_klass_atanasjan/32-1-0-1117/class-10-{num}'
        r = requests.get(link, headers=headers)
        if r.status_code != 200:
            raise ConnectionError
        imgs_block = BeautifulSoup(r.content, 'lxml').find_all(class_='with-overtask')
        imgs = [i.find('img')['src'] for i in imgs_block]
        return [await process(imgs, await GDZ(self.user_id).init()), link]

    async def phiz_megaresheba(self, num: int):
        link = f'https://megaresheba.ru/gdz/fizika/10-klass/kasyanov/{num}-zadacha'
        r = requests.get(link, headers=headers)
        if r.status_code != 200:
            raise ConnectionError
        imgs_block = BeautifulSoup(r.content, 'lxml').find_all(class_='with-overtask')
        imgs = [i.find('img')['src'] for i in imgs_block]
        return [await process(imgs, await GDZ(self.user_id).init()), link]

    async def ang_megaresheba(self, page: int):
        link = f'https://megaresheba.ru/publ/reshebnik/anglijskij/10_klass_spotlight_evans/{page}-str'
        r = requests.get(link, headers=headers)
        if r.status_code != 200:
            raise ConnectionError
        imgs_block = BeautifulSoup(r.content, 'lxml').find(class_='task', id='task').find_next().find_all('img')
        imgs = [i['src'] for i in imgs_block]
        return [await process(imgs, await GDZ(self.user_id).init()), link]

    async def him_putin(self, tem: int, work: int, var: int):
        link = f'https://gdz-putina.fun/json/klass-10/himiya/radeckij/{tem}-{work}-tem-{var}'
        r = requests.get(link, headers=headers)
        data = r.json()['editions'][0]['images']
        imgs = ['https://gdz-putina.fun' + i['url'] for i in data]
        return [await process(imgs, await GDZ(self.user_id).init()), link]

    async def kist(self, page: int):
        if page in [2, 3]:
            return db.kist_ids['ist2']
        elif page in [4, 5]:
            return db.kist_ids['ist4']
        elif page in [6, 7]:
            return db.kist_ids['ist6']
        elif page in [8, 9]:
            return db.kist_ids['ist8']
        elif page in [10, 11]:
            return db.kist_ids['ist10']
        elif page in [12, 13]:
            return db.kist_ids['ist12']
        elif page in [14, 15]:
            return db.kist_ids['ist14']
