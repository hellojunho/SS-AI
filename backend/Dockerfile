FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
COPY cron /app/cron
COPY .env.example /app/.env

ENV PYTHONPATH=/app

RUN chmod +x /app/cron/quiz_cron.sh /app/cron/entrypoint.sh \
    && chmod 0644 /app/cron/quiz-cron \
    && crontab /app/cron/quiz-cron

CMD ["/app/cron/entrypoint.sh"]
