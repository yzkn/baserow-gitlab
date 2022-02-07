#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

# Used by docker-entrypoint.sh to start the dev server
# If not configured you'll receive this: CommandError: "0.0.0.0:" is not a valid port number or address:port pair.
PORT="${PORT:-8000}"
DATABASE_USER="${DATABASE_USER:-baserow}"
DATABASE_HOST="${DATABASE_HOST:-db}"
DATABASE_PORT="${DATABASE_PORT:-5432}"
DATABASE_NAME="${DATABASE_USER:-baserow}"
DATABASE_PASSWORD="${DATABASE_PASSWORD:-baserow}"

BASEROW_AMOUNT_OF_WORKERS=${BASEROW_AMOUNT_OF_WORKERS:-1}
BASEROW_AMOUNT_OF_GUNICORN_WORKERS=${BASEROW_AMOUNT_OF_GUNICORN_WORKERS:-$BASEROW_AMOUNT_OF_WORKERS}
RUN_MINIMAL_CELERY=${RUN_MINIMAL_CELERY:-}

source "/baserow/venv/bin/activate"

postgres_ready() {
python3 << END
import sys
import psycopg2
try:
    psycopg2.connect(
        dbname="${DATABASE_NAME}",
        user="${DATABASE_USER}",
        password="${DATABASE_PASSWORD}",
        host="${DATABASE_HOST}",
        port="${DATABASE_PORT}",
    )
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}

wait_for_postgres() {
until postgres_ready; do
  >&2 echo 'Waiting for PostgreSQL to become available...'
  sleep 1
done
>&2 echo 'PostgreSQL is available'
}



show_help() {
# If you change this please update ./docs/reference/baserow-docker-api.md
    echo """
Usage: docker run [-T] baserow_backend[_dev] COMMAND
Commands
local           : Start django using a prod ready gunicorn server
dev             : Start a normal Django development server
exec            : Exec a command directly
bash            : Start a bash shell
manage          : Start manage.py
setup           : Runs all setup commands (migrate, update_formulas, sync_templates)
python          : Run a python command
shell           : Start a Django Python shell
celery          : Run celery
celery-dev:     : Run a hot-reloading dev version of celery
lint:           : Run the linting (only available if using dev target)
lint-exit       : Run the linting and exit (only available if using dev target)
test:           : Run the tests (only available if using dev target)
ci-test:        : Run the tests for ci including various reports (dev only)
ci-check-startup: Start up a single gunicorn and timeout after 10 seconds for ci (dev).
backup          : Backs up Baserow.
restore         : Restores Baserow.
help            : Show this message
"""
}

curlf() {
  OUTPUT_FILE=$(mktemp)
  HTTP_CODE=$(curl --silent --output "$OUTPUT_FILE" --write-out "%{http_code}" "$@")
  if [[ ${HTTP_CODE} -lt 200 || ${HTTP_CODE} -gt 299 ]] ; then
    >&2 cat "$OUTPUT_FILE"
    return 22
  fi
  cat "$OUTPUT_FILE"
  rm "$OUTPUT_FILE"
}

run_setup_commands_if_configured(){
if [ "$MIGRATE_ON_STARTUP" = "true" ] ; then
  echo "python /baserow/backend/src/baserow/manage.py migrate"
  python /baserow/backend/src/baserow/manage.py migrate
fi
if [ "$SYNC_TEMPLATES_ON_STARTUP" = "true" ] ; then
  echo "python /baserow/backend/src/baserow/manage.py sync_templates"
  python /baserow/backend/src/baserow/manage.py sync_templates
fi
}

start_celery_worker(){
  if [[ -n "$RUN_MINIMAL_CELERY" ]]; then
    EXTRA_CELERY_ARGS=(--without-heartbeat --without-gossip --without-mingle)
  fi
  exec celery -A baserow worker --concurrency "$BASEROW_AMOUNT_OF_WORKERS" "${EXTRA_CELERY_ARGS[@]}" -l INFO "$@"
}

# Lets devs attach to this container running the passed command, press ctrl-c and only
# the command will stop. Additionally they will be able to use bash history to
# re-run the containers command after they have done what they want.
attachable_exec(){
    echo "$@"
    exec bash --init-file <(echo "history -s $*; $*")
}

if [[ -z "${1:-}" ]]; then
  echo "Must provide arguments to docker-entrypoint.sh"
  show_help
  exit 1
fi

case "$1" in
    django-dev)
        wait_for_postgres
        run_setup_commands_if_configured
        echo "Running Development Server on 0.0.0.0:${PORT}"
        echo "Press CTRL-p CTRL-q to close this session without stopping the container."
        attachable_exec python /baserow/backend/src/baserow/manage.py runserver "0.0.0.0:${PORT}"
    ;;
    gunicorn)
        wait_for_postgres
        run_setup_commands_if_configured
        exec gunicorn --workers="$BASEROW_AMOUNT_OF_GUNICORN_WORKERS" \
          --worker-tmp-dir "${TMPDIR:-/dev/shm}" \
          --log-file=- \
          --capture-output \
          --forwarded-allow-ips='*' \
          -b 127.0.0.1:"${PORT}" \
          --log-level=debug \
          -k uvicorn.workers.UvicornWorker baserow.config.asgi:application "${@:2}"
    ;;
    backend-healthcheck)
      echo "Running backend healthcheck..."
      curlf "http://localhost:$PORT/_health/"
    ;;
    exec)
        exec "${@:2}"
    ;;
    bash)
        exec /bin/bash "${@:2}"
    ;;
    manage)
        exec python3 /baserow/backend/src/baserow/manage.py "${@:2}"
    ;;
    python)
        exec python3 "${@:2}"
    ;;
    setup)
      echo "python3 /baserow/backend/src/baserow/manage.py migrate"
      DONT_UPDATE_FORMULAS_AFTER_MIGRATION=yes python3 /baserow/backend/src/baserow/manage.py migrate
      echo "python3 /baserow/backend/src/baserow/manage.py update_formulas"
      python3 /baserow/backend/src/baserow/manage.py update_formulas
      echo "python3 /baserow/backend/src/baserow/manage.py sync_templates"
      python3 /baserow/backend/src/baserow/manage.py sync_templates
    ;;
    shell)
        exec python3 /baserow/backend/src/baserow/manage.py shell
    ;;
    lint-shell)
        attachable_exec make lint-python
    ;;
    lint)
        exec make lint-python
    ;;
    ci-test)
        exec make ci-test-python PYTEST_SPLITS="${PYTEST_SPLITS:-1}" PYTEST_SPLIT_GROUP="${PYTEST_SPLIT_GROUP:-1}"
    ;;
    ci-check-startup)
        exec make ci-check-startup-python
    ;;
    celery)
        exec celery -A baserow  "${@:2}"
    ;;
    celery-worker)
      start_celery_worker -Q celery -n default-worker@%h "${@:2}"
    ;;
    celery-worker-healthcheck)
      echo "Running celery worker healthcheck..."
      exec celery -A baserow inspect ping -d "default-worker@$HOSTNAME" -t 10 "${@:2}"
    ;;
    celery-exportworker)
      start_celery_worker -Q export -n export-worker@%h "${@:2}"
    ;;
    celery-exportworker-healthcheck)
      echo "Running celery export worker healthcheck..."
      exec celery -A baserow inspect ping -d "export-worker@$HOSTNAME" -t 10 "${@:2}"
    ;;
    celery-beat)
      exec celery -A baserow beat -l INFO -S redbeat.RedBeatScheduler "${@:2}"
    ;;
    watch-py)
        # Ensure we watch all possible python source code locations for changes.
        directory_args=''
        for i in $(echo "$PYTHONPATH" | tr ":" "\n")
        do
          directory_args="$directory_args -d=$i"
        done

        attachable_exec watchmedo auto-restart "$directory_args" --pattern=*.py --recursive -- "${BASH_SOURCE[0]} ${*:2}"
    ;;
    backup)
        if [[ -n "${DATABASE_URL:-}" ]]; then
          echo -e "\e[31mThe backup command is currently incompatible with DATABASE_URL, "\
            "please set the DATABASE_{HOST,USER,PASSWORD,NAME,PORT} variables manually"\
            " instead. \e[0m" >&2
          exit 1
        fi
        cd "${DATA_DIR:-/baserow}"/backups || true
        export PGPASSWORD=$DATABASE_PASSWORD
        exec python3 /baserow/backend/src/baserow/manage.py backup_baserow \
            -h "$DATABASE_HOST" \
            -d "$DATABASE_NAME" \
            -U "$DATABASE_USER" \
            -p "$DATABASE_PORT" \
            "${@:2}"
    ;;
    restore)
        if [[ -n "${DATABASE_URL:-}" ]]; then
          echo -e "\e[31mThe restore command is currently incompatible with DATABASE_URL, "\
            "please set the DATABASE_{HOST,USER,PASSWORD,NAME,PORT} variables manually"\
            " instead. \e[0m" >&2
          exit 1
        fi
        cd "${DATA_DIR:-/baserow}"/backups || true
        export PGPASSWORD=$DATABASE_PASSWORD
        exec python3 /baserow/backend/src/baserow/manage.py restore_baserow \
            -h "$DATABASE_HOST" \
            -d "$DATABASE_NAME" \
            -U "$DATABASE_USER" \
            -p "$DATABASE_PORT" \
            "${@:2}"
    ;;
    *)
        echo "${@:2}"
        show_help
        exit 1
    ;;
esac
