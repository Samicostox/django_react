web: gunicorn react_backend.wsgi
release: python manage.py makemigrations --noinput && python manage.py collectstatic --noinput && python manage.py migrate --noinput
