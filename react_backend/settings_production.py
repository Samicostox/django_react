from .settings import *

DEBUG = False

db_from_env = dj_database_url.config(default=os.environ.get('HEROKU_POSTGRESQL_COPPER_URL'), conn_max_age=600)
DATABASES['default'].update(db_from_env)
