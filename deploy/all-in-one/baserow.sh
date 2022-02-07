#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

show_help() {
    echo """
Usage: docker run --rm --it [-v baserow:$DATA_DIR] baserow COMMAND_FROM_BELOW
Commands
start           : Launches baserow with all services running internally in a single
                  container.
web-frontend    : Show all available one-off web-frontend commands.
backend         : Show all available one-off backend commands.
backend_with_db : Starts the embedded postgres database and then runs any supplied
                  backend command normally. Useful for running one off commands that
                  require the database like backups and restores.
db_only         : Starts up only the embedded postgres server and makes it available
                  for external connections if you expose port 5432 using
                  the extra docker run argument of '-p 5432:5432'. Useful for if you
                  need to manually inspect Baserows database etc.
help            : Show this message.
"""
}
if [[ -z "${1:-}" ]]; then
  echo "Must provide arguments to baserow"
  show_help
  exit 1
fi

source /baserow/supervisor/default_baserow_env.sh
shopt -s nullglob
for f in /baserow/supervisor/env/*.sh; do
   echo "Importing extra settings from $f"
    # shellcheck disable=SC1090
    source "$f";
done
for f in "$DATA_DIR"/env/*.sh; do
   echo "Importing extra data dir settings from $f"
    # shellcheck disable=SC1090
    source "$f";
done

ensure_db(){
  if [[ $$ -ne 1 || $(pgrep -f "postgres") ]]; then
      echo -e "\e[31mPlease do not run the db_only or backend_with_db ccommands in an "\
      "existing Baserow container as they are designed to be standalone. Please use "\
      "docker run instead of exec or just the normal 'backend' command.\e[0m" >&2
      exit 1
  fi
  if [[ "$DATABASE_HOST" == "localhost" && -z "${DATABASE_URL:-}" ]]; then
    echo "No DATABASE_HOST or DATABASE_URL provided, using embedded postgres."
    echo "Ensuring default baserow database available."
    export DATABASE_PASSWORD=baserow
    export DATABASE_HOST=localhost
      POSTGRES_USER=$DATABASE_USER \
      POSTGRES_PASSWORD=$DATABASE_PASSWORD \
      POSTGRES_DB=$DATABASE_NAME \
      /baserow/supervisor/docker-postgres-setup.sh
    pg_ctlcluster 11 main start
  else
    echo -e "\e[31mEither DATABASE_HOST or DATABASE_URL has been set\e[0m" >&2
    exit 1
  fi
  function finish {
    if [[ "$DATABASE_HOST" == "localhost" && -z "${DATABASE_URL:-}" ]]; then
     echo "Stopping db"
      pg_ctlcluster 11 main stop
    fi
  }
  trap finish EXIT
}

docker_safe_run(){
    exec tini -s -- gosu baserow_docker_user "$@"
}

# Setup the various folders in the data mount with the correct permissions.
# We do this here instead of in the docker image incase the user mounts in a host
# directory as a volume, which will not be auto setup by docker with the containers
# underlying structure.

mkdir -p "$DATA_DIR"/redis
chown redis:redis "$DATA_DIR"/redis

mkdir -p "$DATA_DIR"/caddy
chown caddy:caddy "$DATA_DIR"/caddy

mkdir -p "$DATA_DIR"/postgres
chown postgres:postgres "$DATA_DIR"/postgres

mkdir -p "$DATA_DIR"/media
chown baserow_docker_user:baserow_docker_group "$DATA_DIR"/media
mkdir -p "$DATA_DIR"/env
chown baserow_docker_user:baserow_docker_group "$DATA_DIR"/env
mkdir -p "$DATA_DIR"/backups
chown baserow_docker_user:baserow_docker_group "$DATA_DIR"/backups

# TODO think about secrets
if [[ ! -f "$DATA_DIR"/.secret && -z "${SECRET_KEY:-}" ]]; then
    echo "export SECRET_KEY=$(tr -dc 'a-z0-9' < /dev/urandom | head -c50)" > "$DATA_DIR"/.secret
fi
source /baserow/data/.secret

case "$1" in
    start)
      exec /baserow/supervisor/start.sh "${@:2}"
    ;;
    backend_with_db)
      export NO_MODEL_CACHE=yes
      ensure_db
      docker_safe_run  ./baserow/backend/docker/docker-entrypoint.sh "${@:2}"
    ;;
    db_only)
      ensure_db
      # Run this temporary server with its own pg_hba.conf so if the above check somehow
      # fails we don't accidentally edit the pg_hba.conf of the normal embedded postgres
      # which we don't want exposed at all.
      TMP_HBA_FILE=/etc/postgresql/11/main/pg_hba_temp.conf
      cp -p /etc/postgresql/11/main/pg_hba.conf "$TMP_HBA_FILE"

      HBA_ENTRY="host    all             all             all                     md5"
      echo "$HBA_ENTRY" \
        | tee -a "$TMP_HBA_FILE"

      exec tini -s -- gosu postgres \
            /usr/lib/postgresql/11/bin/postgres \
            -c config_file=/etc/postgresql/11/main/postgresql.conf \
            -c listen_addresses='*' \
            -c hba_file="$TMP_HBA_FILE"
    ;;
    backend)
      docker_safe_run /baserow/backend/docker/docker-entrypoint.sh "${@:2}"
    ;;
    web-frontend)
      docker_safe_run /baserow/web-frontend/docker/docker-entrypoint.sh "${@:2}"
    ;;
    *)
        echo "${@:2}"
        show_help
        exit 1
    ;;
esac
