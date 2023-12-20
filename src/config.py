from psycopg2 import OperationalError
from sqdb import Sqdb
from dotenv import load_dotenv
from os import environ

load_dotenv()
token = environ['API_TOKEN']
proxy = environ['PROXY']
futureforge_api = environ['FUTUREFORGE_API']
try:
    sql = Sqdb(environ['SQL_HOST'], environ['SQL_PASSWORD'], environ['SQL_PORT'], environ['SQL_DATABASE'], environ['SQL_USER'])
except OperationalError:
    sql = None
    print('COULD NOT CONNECT TO DATABASE!\n' * 5)