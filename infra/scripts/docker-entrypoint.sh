#!/bin/sh
set -eu

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
  python manage.py migrate --noinput
  if [ "${SEED_DEMO:-1}" = "1" ]; then
    python manage.py seed_demo
  fi
fi
python manage.py collectstatic --noinput >/dev/null 2>&1 || true
exec "$@"
