#!/bin/sh
set -e

cron
if [ "${DEV_RELOAD:-0}" = "1" ] || [ "${DEV_RELOAD}" = "true" ]; then
	exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
	exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
