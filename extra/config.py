import os

from psycopg2 import OperationalError
from database.sqdb import Sqdb
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('API_TOKEN')
proxy = os.getenv('PROXY')
futureforge_api = os.getenv('FUTUREFORGE_API')
wolfram_api = os.getenv('WOLFRAM_API')
gigachat_api = os.getenv('GIGACHAT_API')

try:
    sql = Sqdb(os.getenv('SQL_HOST'), os.getenv('SQL_PASSWORD'), os.getenv('SQL_PORT'), os.getenv('SQL_DATABASE'), os.getenv('SQL_USER'))
except OperationalError:
    sql = None
    print('COULD NOT CONNECT TO DATABASE!\n' * 5)
