import psycopg2


class Sqdb:
    def __init__(self, host, password, port, database, user):
        self.connection = psycopg2.connect(host=host,
                                           password=password,
                                           port=port,
                                           database=database,
                                           user=user)
        self.cursor = self.connection.cursor()

    def is_user_exists(self, user_id):
        with self.connection:
            self.cursor.execute(f"SELECT COUNT(*) from users WHERE user_id = {user_id}")
            if_exist = self.cursor.fetchone()
            return if_exist[0]

    def add_user(self, user_id, username, user_name, user_surname, upscaled=False):
        if not (Sqdb('containers-us-west-126.railway.app', '4LqiTuqiRbofen68DIm5', '6466', 'railway', 'postgres').is_user_exists(user_id)):
            with self.connection:
                self.cursor.execute(
                    f"INSERT INTO users (user_id, username, user_name, user_surname, upscaled) VALUES ({user_id}, '{username}', '{user_name}', '{user_surname}', {upscaled})")
                return True
        else:
            return False

    def get_data(self, user_id, data):
        with self.connection:
            self.cursor.execute(f'SELECT {data} FROM users WHERE user_id = {user_id}')
            return self.cursor.fetchone()[0]
