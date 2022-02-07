#!/usr/bin/env bash
set -Eeo pipefail


# Use https://manytools.org/hacker-tools/ascii-banner/ and the font ANSI Banner / Wide / Wide to generate
cat << EOF
=========================================================================================

██████╗  █████╗ ███████╗███████╗██████╗  ██████╗ ██╗    ██╗     ██╗    █████╗    ██████╗
██╔══██╗██╔══██╗██╔════╝██╔════╝██╔══██╗██╔═══██╗██║    ██║    ███║   ██╔══██╗   ╚════██╗
██████╔╝███████║███████╗█████╗  ██████╔╝██║   ██║██║ █╗ ██║    ╚██║   ╚█████╔╝    █████╔╝
██╔══██╗██╔══██║╚════██║██╔══╝  ██╔══██╗██║   ██║██║███╗██║     ██║   ██╔══██╗   ██╔═══╝
██████╔╝██║  ██║███████║███████╗██║  ██║╚██████╔╝╚███╔███╔╝     ██║██╗╚█████╔╝██╗███████╗
╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚══╝╚══╝      ╚═╝╚═╝ ╚════╝ ╚═╝╚══════╝

=========================================================================================

This is the Baserow all in one Docker image. By default it runs all Baserow services
within a single container.

=== Customization ==

======== USING AN EXTERNAL POSTGRESQL =======

Set DATABASE_HOST, DATABASE_PASSWORD, DATABASE_USER to configure Baserow to use an
external postgres database instead of using its own internal one.

======== USING AN EXTERNAL REDIS =======

Set REDIS_HOST to configure Baserow to use an external redis instead of using its own
internal one.

======== SETTING A DOMAIN NAME AND AUTOMATIC HTTPS =========

Set DOMAIN if you want Baserow to be available at a configured domain name. Internally
Baserow is using a caddy reverse proxy which will automatically provision SSL
certificates if DOMAIN is publicly accessible by certbot. For this to work you must
ensure:

* You are running this docker container with ports 80 and 443 exposed and bound ( -p 80:80 -p 443:443)
* You are running this docker container with the DOMAIN env variable set (-e DOMAIN=www.yourbaserow.com)
* Your domain's A/AAAA records point to your server
* Ports 80 and 443 are open externally

See https://caddyserver.com/docs/automatic-https for more info

======== FOR MORE HELP ========

For help, feedback and suggestions please post at https://community.baserow.io

TODO
1. Ensure DOMAIN variable + all the others make sense
2. Provide a better way of managing secrets
   -> postgres password
   -> django secret key
3. Cleanup docs
4. Warn if running in local mode and potentially exposed to the internet.
EOF

if [[ -z "$DISABLE_VOLUME_CHECK" ]]; then
  mountVar=$(mount | grep "$DATA_DIR" || true)
  if [ -z "$mountVar" ]
  then
  echo -e "\e[33mPlease run baserow with a mounted data folder " \
          "'docker volume create baserow_data && docker run -v " \
          "baserow_data:/baserow/data ...', otherwise your data will be lost between " \
          "runs. To disable this check set the DISABLE_VOLUME_CHECK env variable to " \
          "'yes' (docker run -e DISABLE_VOLUME_CHECK=yes ...). \e[0m"
  exit 1
  fi
fi


startup_echo(){
  ./baserow/supervisor/wrapper.sh STARTUP echo -e "\e[32m$*\e[0m"
}

SUPERVISOR_DISABLED_CONF_DIR=/baserow/supervisor/includes/disabled
SUPERVISOR_ENABLED_CONF_DIR=/baserow/supervisor/includes/enabled

if [[ "$DATABASE_HOST" == "localhost" && -z "${DATABASE_URL:-}" ]]; then
  startup_echo "No DATABASE_HOST or DATABASE_URL provided, using embedded postgres."
  startup_echo "Ensuring default baserow database available."
  export DATABASE_PASSWORD=baserow
  export DATABASE_HOST=localhost
  PGDATA="$DATA_DIR/postgres/" \
    POSTGRES_USER=$DATABASE_USER \
    POSTGRES_PASSWORD=$DATABASE_PASSWORD \
    POSTGRES_DB=$DATABASE_NAME \
    ./baserow/supervisor/wrapper.sh POSTGRES_INIT ./baserow/supervisor/docker-postgres-setup.sh

  # Enable the embedded postgres by moving it into the directory from which supervisor
  # includes all .conf files it finds.
  mv "$SUPERVISOR_DISABLED_CONF_DIR/embedded-postgres.conf" "$SUPERVISOR_ENABLED_CONF_DIR/embedded-postgres.conf"
else
  # Disable the embedded postgres if somehow the conf is in the enabled folder
  mv "$SUPERVISOR_ENABLED_CONF_DIR/embedded-postgres.conf" "$SUPERVISOR_DISABLED_CONF_DIR/embedded-postgres.conf" 2>/dev/null
  startup_echo "Using provided external postgres at ${DATABASE_HOST:-} ${DATABASE_URL:-}"
fi

if [[ "$REDIS_HOST" == "localhost" && -z "${REDIS_URL:-}" ]]; then
  startup_echo "Using embedded baserow redis as no REDIS_HOST or REDIS_URL provided. "
  # Enable the embedded redis by moving it into the directory from which supervisor
  # includes all .conf files it finds.
  mv "$SUPERVISOR_DISABLED_CONF_DIR/embedded-redis.conf" "$SUPERVISOR_ENABLED_CONF_DIR/embedded-redis.conf"
else
  # Disable the embedded redis if somehow the conf is in the enabled folder
  mv "$SUPERVISOR_ENABLED_CONF_DIR/embedded-redis.conf" "$SUPERVISOR_DISABLED_CONF_DIR/embedded-redis.conf" 2>/dev/null
  startup_echo "Using provided external redis at ${REDIS_HOST:-} ${REDIS_URL:-}"
fi

if [[ "$DOMAIN" == "http://localhost:80" ]]; then
  startup_echo "No DOMAIN environment variable provided. Starting baserow locally at http://localhost without automatic https."
else
  startup_echo "Starting Baserow using external domain name $DOMAIN, will automatically attempt to enable SSL via caddy."
fi

startup_echo "Starting all Baserow processes:"
exec /usr/bin/supervisord --configuration /baserow/supervisor/supervisor.conf
