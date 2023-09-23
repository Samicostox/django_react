from .settings import *


DEBUG = False

DATABASES = {
    'default': dj_database_url.config(default=os.environ.get('HEROKU_POSTGRESQL_COPPER_URL'), conn_max_age=600)
}