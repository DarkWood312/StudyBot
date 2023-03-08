import netschoolapi.errors
from netschoolapi import NetSchoolAPI
from async_class import AsyncClass
from datetime import date

class NetSchool(AsyncClass):
    async def __ainit__(self, login, password, school_id=4596, url='https://sgo.rso23.ru/'):
        self.login = login
        self.password = password
        self.school_id = school_id
        self.url = url

        self.ns = NetSchoolAPI(url)
        await self.ns.login(self.login, self.password, self.school_id)

        self.start_date = date(2023, 1, 9)

    async def get_ns(self):
        return self.ns

    async def logout(self):
        await self.ns.logout()
        return True

    async def get_marks(self, start_date: date = None) -> dict:
        if start_date is None:
            start_date = self.start_date

        diary = await self.ns.diary(start=start_date, end=date.today())
        schedule = diary.schedule
        list_ = []
        dict_ = {}

        for day in schedule:
            for lesson in day.lessons:
                for assignment in lesson.assignments:
                    if assignment.mark is not None:
                        if assignment.type.lower() in ['контрольная работа']:
                            marks = [assignment.mark] * 3
                        elif assignment.type.lower() in ['практическая работа', 'лабораторная работа', 'сочинение']:
                            marks = [assignment.mark] * 2
                        elif assignment.type.lower() in ['ответ на уроке', 'домашнее задание', 'работа на уроке',
                                                         'работа с контурными картами', 'словарный диктант']:
                            marks = [assignment.mark]
                        else:
                            marks = [assignment.mark]

                        list_.append({lesson.subject: marks})
                        if lesson.subject in list(dict_.keys()):
                            old_data = dict_[lesson.subject]
                        else:
                            old_data = []
                        old_data.append(marks[0])
                        dict_[lesson.subject] = old_data

        await self.ns.logout()
        return dict_