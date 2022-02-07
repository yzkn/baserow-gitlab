#!/bin/bash

set -eu

export DOMAIN=${BASEROW_PUBLIC_URL:-https://$HEROKU_APP_NAME.herokuapp.com}
# Only listen to the port with caddy to disable its automatic ssl
export CADDY_LISTEN_PORT=":$PORT"
export REDIS_URL=${REDIS_TLS_URL:-$REDIS_URL}
export DJANGO_SETTINGS_MODULE='baserow.config.settings.heroku'
export RUN_MINIMAL_CELERY=yes
