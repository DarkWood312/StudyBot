import os

from psycopg2 import OperationalError
from database.sqdb import Sqdb
from dotenv import load_dotenv
from loguru import logger

load_dotenv()
token = os.getenv('API_TOKEN')
openai_api = os.getenv('OPENAI_API') or None
wolfram_api = os.getenv('WOLFRAM_API') or None
uchus_cookies = {k: v for k, v in [i.split('=', 1) for i in os.getenv('UCHUS_COOKIES').split(';')]} or None
redis_host, redis_password, redis_port = os.getenv('REDIS_HOST') or None, os.getenv('REDIS_PASSWORD') or None, os.getenv('REDIS_PORT') or '5432'
deep_translate_api = os.getenv('DEEP_TRANSLATE_API') or None

try:
    sql = Sqdb(os.getenv('SQL_HOST'), os.getenv('SQL_PASSWORD'), os.getenv('SQL_PORT'), os.getenv('SQL_DATABASE'), os.getenv('SQL_USER'))
except OperationalError:
    sql = None
    logger.error('COULD NOT CONNECT TO DATABASE!\n' * 5)
