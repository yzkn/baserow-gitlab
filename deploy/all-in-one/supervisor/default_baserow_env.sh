#!/usr/bin/env bash

export DOCKER_USER=${DOCKER_USER:-baserow_docker_user}
export DATA_DIR=${DATA_DIR:-/baserow/data}

export BASEROW_AMOUNT_OF_WORKERS=${BASEROW_AMOUNT_OF_WORKERS:-1}
export BASEROW_AMOUNT_OF_GUNICORN_WORKERS=${BASEROW_AMOUNT_OF_GUNICORN_WORKERS:-$BASEROW_AMOUNT_OF_WORKERS}

export CADDY=on

export PYTHONUNBUFFERED=1
export PYTHONPATH="${PYTHONPATH:-}:/baserow/backend/src:/baserow/premium/backend/src"
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
export TMPDIR=${TMPDIR:-/dev/shm}

export DATABASE_PASSWORD="${DATABASE_PASSWORD:-baserow}"
export DATABASE_NAME="${DATABASE_NAME:-baserow}"
export DATABASE_USER="${DATABASE_USER:-baserow}"
export DATABASE_HOST="${DATABASE_HOST:-localhost}"
export DATABASE_PORT="${DATABASE_PORT:-5432}"
export PGDATA="$DATA_DIR/postgres/"

export REDIS_HOST="${REDIS_HOST:-localhost}"

export DOMAIN="${DOMAIN:-"http://localhost:80"}"
export CADDY_LISTEN_PORT="${CADDY_LISTEN_PORT:-}"


export PRIVATE_BACKEND_URL='http://localhost:8000'
export PRIVATE_WEBFRONTEND_URL='http://localhost:3000'

export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-'baserow.config.settings.base'}
export SYNC_TEMPLATES_ON_STARTUP=${SYNC_TEMPLATES_ON_STARTUP:-true}
export MIGRATE_ON_STARTUP=${MIGRATE_ON_STARTUP:-true}
export MEDIA_ROOT="$DATA_DIR/media"

