import json

import psycopg2
import asyncpg


class Sqdb:
    def __init__(self, host, password, port, database, user):
        self.connection = psycopg2.connect(host=host,
                                           password=password,
                                           port=port,
                                           database=database,
                                           user=user)
        self.cursor = self.connection.cursor()

    async def is_user_exists(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT COUNT(*) from users WHERE user_id = {user_id}")
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

    async def get_data(self, user_id, data):
        with self.connection:
            self.cursor.execute(f'SELECT {data} FROM users WHERE user_id = {user_id}')
            return self.cursor.fetchone()[0]

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

    async def change_data(self, user_id, name, data):
        with self.connection:
            self.cursor.execute(f"UPDATE users set {name} = '{data}' WHERE user_id = {user_id}")

    async def change_data_type(self, user_id, name, data):
        with self.connection:
            self.cursor.execute(f'UPDATE users set {name} = {data} WHERE user_id = {user_id}')

    async def change_data_jsonb(self, user_id, name: str, data: dict):
        data = json.dumps(data)
        with self.connection:
            self.cursor.execute(f'UPDATE users set {name} = %s::jsonb WHERE user_id = %s', (data, user_id))

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
            sorted_result = sorted({i[0]: i[1] for i in result}.items(), reverse=True, key=lambda x:x[1])[:maximum]
            dict_res = {j[0]: j[1] for j in sorted_result}
            return dict_res
