from difflib import get_close_matches

import requests
from bs4 import BeautifulSoup

from config import sql

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 '
                  'Safari/537.36 ',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
              'application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
}


class ModernGDZ:
    def __init__(self, user_id):
        self.status = None
        self.user_id = user_id
        self.gdzputinafun = self.GdzPutinaFun()

    async def get_user_id(self):
        self.status = bool(await sql.get_data(self.user_id, 'upscaled'))
        return self.status

    # async def process(self, arr, doc: bool = None):
    #     if not isinstance(arr, list):
    #         sep = 4096
    #         l = arr
    #     else:
    #         if doc is None:
    #             doc = await self.get_user_id()
    #         sep = 10
    #         if doc:
    #             l = [types.InputMediaDocument(media=i) for i in arr]
    #         else:
    #             l = [types.InputMediaPhoto(media=i) for i in arr]
    #     return [l[i:i + sep] for i in range(0, len(l), sep)]

    class GdzPutinaFun:
        def __init__(self):
            self.main_url = 'https://gdz-putina.fun'

        async def get_subjects(self) -> dict:
            grades_dict = {}
            subjects = {}

            r = requests.get(self.main_url, headers=headers)
            grades = BeautifulSoup(r.content, 'lxml').find(class_='siteMenu').find_all(class_='classesSelect')

            for grade in grades:
                grade_num = grade.find('div').find('a').get('href')[1:]

                for subject in grade.find('ul').find_all('li'):
                    subject_url = subject.find('a').get('href')

                    subjects[subject.find('a').getText().strip()] = self.main_url + subject_url

                grades_dict[grade_num] = subjects
                subjects = {}

            return grades_dict

        async def get_subject_url(self, query_grade: int | str, query_subject: str) -> dict:
            subjects = (await self.get_subjects())[f'klass-{query_grade}']
            defined_subject = get_close_matches(query_subject, subjects, 1)[0]
            url = subjects[defined_subject]
            return url

        async def get_books(self, url) -> list:
            r = requests.get(url, headers=headers)
            books =BeautifulSoup(r.content, 'lxml').find(class_='box').find_all('a', class_='book')
            books_list = []

            for book in books:
                img_content = book.find('img')
                img_url = self.main_url + img_content.get('data-src')
                img_title = img_content.get('alt')
                book_url_without_main = book.get('href')
                book_url = self.main_url + book_url_without_main
                authors = ': '.join([a.strip() for a in book.find(class_='authors-in-category').getText().split(':', 1)])
                book_dict = {
                    'img_url': img_url,
                    'img_title': img_title,
                    'book_url': book_url,
                    'main_url': self.main_url,
                    'book_without_class': book_url_without_main.split('/', 2)[-1],
                    'class_url': self.main_url + book_url.split('/', 2)[1],
                    'author': authors.upper()
                }
                books_list.append(book_dict)

            return books_list

        async def gdz(self, url, num) -> list:
            main_content = requests.get(url, headers=headers)
            task_call = BeautifulSoup(main_content.content, 'lxml').find('div', class_='tasks').find('ul', class_='structure').find(class_='structure-item').find('a').get('href').replace('#task?t=', '')[1:]
            modified_url = url.replace('https://gdz-putina.fun/', 'https://gdz-putina.fun/json/') + f'/{num}{task_call}'
            r = requests.get(modified_url, headers=headers)
            editions = r.json()['editions']
            data = []
            for edition in editions:
                for image in edition['images']:
                    data.append(image['url'])
            imgs = [self.main_url + img_url for img_url in data]
            # return [imgs, url] url is json
            return imgs
