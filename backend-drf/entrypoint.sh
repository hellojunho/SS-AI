#!/bin/sh
set -e

echo "Waiting for MySQL to be ready..."
max_retries=30
count=0
until python -c "import pymysql; pymysql.connect(host='db', port=3306, user='ss_ai', password='ss_ai', database='ss_ai')" 2>/dev/null; do
  count=$((count + 1))
  if [ $count -ge $max_retries ]; then
    echo "MySQL connection timeout after $max_retries attempts"
    exit 1
  fi
  echo "MySQL is unavailable - sleeping (attempt $count/$max_retries)"
  sleep 2
done

echo "MySQL is ready - executing commands"
python manage.py migrate --run-syncdb --noinput
python manage.py bootstrap_ss_ai
exec python manage.py runserver 0.0.0.0:8080
