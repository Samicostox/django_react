release: python manage.py makemigrations --noinput && python manage.py collectstatic --noinput && python manage.py migrate --noinput
web: gunicorn react_backend.wsgi
worker: celery -A react_backend worker --loglevel=info
