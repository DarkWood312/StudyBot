import json
import typing
from dataclasses import dataclass

import psycopg2
import asyncpg


@dataclass(frozen=True)
class UchusOnlineSettings:
    user_id: int
    min_complexity: int
    max_complexity: int
    complexity_asc: bool


class Sqdb:
    def __init__(self, host, password, port, database, user):
        self.connection = psycopg2.connect(host=host,
                                           password=password,
                                           port=port,
                                           database=database,
                                           user=user)
        self.cursor = self.connection.cursor()

    async def is_user_exists(self, user_id, table='users'):
        with self.connection:
            self.cursor.execute(f"SELECT COUNT(*) from {table} WHERE user_id = {user_id}")
            if_exist = self.cursor.fetchone()
            return if_exist[0]

    async def add_user(self, user_id, username, user_name, user_surname):
        with self.connection:
            self.cursor.execute(f"SELECT COUNT(*) from users WHERE user_id = {user_id}")
            if_exist = self.cursor.fetchone()[0]
            if not if_exist:
                self.cursor.execute(
                    f"INSERT INTO users (user_id, username, user_name, user_surname) VALUES ({user_id}, '{username}', '{user_name}', '{user_surname}')")
                return True
            else:
                self.cursor.execute(
                    f"UPDATE users set username = '{username}', user_name = '{user_name}', user_surname = '{user_surname}' WHERE user_id = {user_id}")
                return False

    async def get_data(self, user_id, data, table='users'):
        with self.connection:
            self.cursor.execute(f'SELECT {data} FROM {table} WHERE user_id = {user_id}')
            return self.cursor.fetchone()[0]

    async def get_all_data(self, user_id, table='users'):
        with self.connection:
            self.cursor.execute(f'SELECT * FROM {table} WHERE user_id = {user_id}')
            return self.cursor.fetchall()[0]

    async def get_wordcloud_settings(self, user_id) -> typing.Dict[str, str | int]:
        with self.connection:
            self.cursor.execute(f'SELECT * FROM wordcloud_settings WHERE user_id = {user_id}')
            data = self.cursor.fetchall()[0]
            wc_user_settings = {
                'background_color': data[1],
                'colormap': data[2],
                'scale': data[3],
                'width': data[4],
                'height': data[5],
                'min_font_size': data[6],
                'max_font_size': data[7],
                'max_words': data[8]
            }
            return wc_user_settings

    async def get_uchus_settings(self, user_id) -> UchusOnlineSettings:
        with self.connection:
            self.cursor.execute(f'SELECT * FROM uchus_online WHERE user_id = {user_id}')
            data = self.cursor.fetchall()[0]
            return UchusOnlineSettings(*data[:-1])

    async def add_uchus_user(self, user_id):
        if_exist = await self.is_user_exists(user_id=user_id, table='uchus_online')
        if not if_exist:
            with self.connection:
                self.cursor.execute(f"INSERT INTO uchus_online (user_id) VALUES ({user_id})")

    # async def get_logpass(self, user_id) -> dict | None:
    #     with self.connection:
    #         self.cursor.execute(f'SELECT netschool FROM users WHERE user_id = {user_id}')
    #         data = self.cursor.fetchone()[0]
    #         if data is None:
    #             return None
    #         k, v = data.split(':::')
    #         return {'login': k, 'password': v}

    async def get_admins(self):
        with self.connection:
            self.cursor.execute('SELECT user_id FROM users WHERE admin = TRUE')
            return [i[0] for i in self.cursor.fetchall()]

    async def get_users(self):
        with self.connection:
            self.cursor.execute('SELECT * FROM users')
            return self.cursor.fetchall()

    # async def get_data_table(self, mark_data, mark_name='description', data='file_id', table='docs'):
    #     with self.connection:
    #         self.cursor.execute(f"SELECT {data} FROM {table} WHERE {mark_name} = '{mark_data}'")
    #         return self.cursor.fetchone()[0]

    # ! Deprecated
    # async def update_data(self, user_id, name, data: str, table='users'):
    #     with self.connection:
    #         self.cursor.execute(f"UPDATE {table} set {name} = '{data}' WHERE user_id = {user_id}")

    # ! Deprecated
    # async def change_data_type(self, user_id, name, data, table='users'):
    #     with self.connection:
    #         self.cursor.execute(f'UPDATE {table} set {name} = {data} WHERE user_id = {user_id}')

    # ! Deprecated
    # async def change_data_jsonb(self, user_id, name: str, data: dict, table='users'):
    #     data = json.dumps(data)
    #     with self.connection:
    #         self.cursor.execute(f'UPDATE {table} set {name} = %s::jsonb WHERE user_id = %s', (data, user_id))

    async def update_data(self, user_id, name: str, data, table='users'):
        if isinstance(data, dict):
            data = json.dumps(data)
        with self.connection:
            self.cursor.execute(f'UPDATE {table} set {name} = %s WHERE user_id = %s', (data, user_id))

    async def add_orthoepy(self, word: str, counter: int = 1):
        with self.connection:
            self.cursor.execute(f"SELECT COUNT(*) FROM orthoepy_problems WHERE word = '{word}'")
            if_exist = self.cursor.fetchone()[0]
            if not if_exist:
                self.cursor.execute(f"INSERT INTO orthoepy_problems (word, counter) VALUES ('{word}', {counter})")
                return True
            else:
                self.cursor.execute(f"SELECT counter FROM orthoepy_problems WHERE word = '{word}'")
                current_counter = self.cursor.fetchone()[0]
                self.cursor.execute(
                    f"UPDATE orthoepy_problems set counter = {current_counter + counter} WHERE word = '{word}'")
                return False

    async def get_orthoepy(self, maximum: int) -> dict:
        with self.connection:
            self.cursor.execute(f"SELECT * FROM orthoepy_problems")
            result = self.cursor.fetchall()
            sorted_result = sorted({i[0]: i[1] for i in result}.items(), reverse=True, key=lambda x: x[1])[:maximum]
            dict_res = {j[0]: j[1] for j in sorted_result}
            return dict_res

    async def add_wordcloud_user(self, user_id: int):
        if_exist = await self.is_user_exists(user_id=user_id, table='wordcloud_settings')
        if not if_exist:
            with self.connection:
                self.cursor.execute(f"INSERT INTO wordcloud_settings (user_id) VALUES ({user_id})")
