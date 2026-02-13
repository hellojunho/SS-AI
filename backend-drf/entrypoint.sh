#!/bin/sh
set -e

python manage.py migrate --run-syncdb --noinput
python manage.py bootstrap_ss_ai
exec python manage.py runserver 0.0.0.0:8000
