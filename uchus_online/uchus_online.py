import io
import re
import textwrap
import typing
from dataclasses import dataclass
from io import BytesIO
from typing import Dict

import aiohttp
from bs4 import BeautifulSoup
from matplotlib import pyplot as plt

from extra import exceptions


@dataclass(frozen=True)
class Task:
    content: str
    img: str | None
    difficulty: int
    resolution: str


class UchusOnline:
    def __init__(self, session: aiohttp.client.ClientSession, PHPSESSID: str):
        self.session = session
        self.base_url = 'https://uchus.online'
        self.headers = {'Host': 'uchus.online',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
                        'Cookie': f'PHPSESSID={PHPSESSID}',
                        'Connection': 'keep-alive'}
        self.cookies = {'PHPSESSID': PHPSESSID}
        self.have_csrf = False

    @property
    async def csrf(self) -> True:
        async with self.session.get(self.base_url, headers=self.headers) as response:
            csrf = response.cookies.get('_csrf').value
            csrf_token = BeautifulSoup(await response.text(), 'lxml').find('meta', attrs={'name': 'csrf-token'}).get(
                'content')

        self.cookies['_csrf'] = csrf
        self.headers['Cookie'] = ';'.join([f'{k}={v}' for k, v in self.cookies.items()])
        self.headers['X-CSRF-Token'] = csrf_token

        self.have_csrf = True
        return True

    async def get_banks_id(self, query: str = 'ЕГЭ профиль') -> dict[str, str]:
        if not self.have_csrf:
            await self.csrf

        async with self.session.get(self.base_url) as response:
            soup = BeautifulSoup(await response.text(), 'lxml')
        target = soup.find(text=re.compile(query))
        submenu = target.find_next('ul', class_='submenu').find_all('li')
        data = {i.find('span').getText().lower(): self.base_url + i.find('a').get('href') for i in submenu}
        return data

    async def get_tasks(self, bank_url: str, pages: int = 1,
                        search_type: typing.Literal['complexity_asc', 'complexity_desc'] = 'complexity_asc',
                        min_complexity: int = 0,
                        max_complexity: int = 100) -> dict[int, Task]:
        if not self.have_csrf:
            await self.csrf

        params = {k: v for k, v in list(locals().items())[3:]}
        tasks = {}
        for page in range(1, pages + 1):
            params['page'] = page
            async with self.session.get(bank_url, params=params) as response:
                soup = BeautifulSoup(await response.text(), 'lxml')
            task_blocks = soup.find_all('div', class_='task-block')
            for task in task_blocks:
                t = task.find(class_='panel-body').find('p')
                task_id = task.get('id').replace('task_', '')
                difficulty = int(task.find(class_='badge').getText()[:-1])
                img = (self.base_url + task.find('img').get('src')) if task.find('img') is not None else None
                # tasks[int(task_id)] = t.getText().replace('\\(', '$').replace('\\)', '$'), img, difficulty, await self.get_resolution(task_id)
                tasks[int(task_id)] = Task(t.getText().replace('\\(', '$').replace('\\)', '$'), img, difficulty, await self.get_resolution(task_id))

        return tasks

    async def get_resolution(self, task_id: int) -> str:
        if not self.have_csrf:
            await self.csrf

        async with self.session.post(f'{self.base_url}/tasks/resolution/{task_id}', headers=self.headers) as response:
            embed_url = BeautifulSoup(await response.text(), 'lxml').find('iframe').get('src').replace('\\"', '')
        return f'https://youtube.com/watch?v={embed_url.split("embed/")[1].replace("?", "&")}'

    async def answer(self, task_id: int, answer: str) -> bool:
        if not self.have_csrf:
            await self.csrf

        response = await self.session.post(self.base_url + f'/tasks/check/{task_id}', headers=self.headers, cookies=self.cookies,
                                           data={'_csrf': self.headers['X-CSRF-Token'], 'answer': answer})
        res = await response.json()
        if response.status != 200:
            raise exceptions.UchusOnlineException.Unauthorized(res)
        response.close()
        return res['result']
