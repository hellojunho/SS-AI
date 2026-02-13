FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

ENV PYTHONPATH=/app

RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
