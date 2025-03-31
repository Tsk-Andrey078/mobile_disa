#!/bin/bash
set -e

echo "Collecting static files"
python manage.py collectstatic --noinput

echo "Starting"
exec gunicorn -k gevent -w 4 -t 900 --bind 0.0.0.0:8000 mobile_prj.wsgi:application --log-level=debug
