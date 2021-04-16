#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail
IFS=$'\n\t'


tabname() {
  printf "\e]1;$1\a"
}

print_manual_instructions(){
  COMMAND=$1
  echo -e "\nTo inspect the now running dev environment open a new tab/terminal and run:"
  echo "    $COMMAND"
}

PRINT_WARNING=true
new_tab() {
  TAB_NAME=$1
  COMMAND=$2

  if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ -x "$(command -v gnome-terminal)" ]; then
      gnome-terminal \
      --tab --title="$TAB_NAME" --working-directory="$(pwd)" -- /bin/bash -c "$COMMAND"
    else
      if $PRINT_WARNING; then
          echo -e "\nWARNING: gnome-terminal is the only currently supported way of opening
          multiple tabs/terminals for linux by this script, add support for your setup!"
          PRINT_WARNING=false
      fi
      print_manual_instructions "$COMMAND"
    fi
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    osascript \
        -e "tell application \"Terminal\"" \
        -e "tell application \"System Events\" to keystroke \"t\" using {command down}" \
        -e "do script \"printf '\\\e]1;$TAB_NAME\\\a'; $COMMAND\" in front window" \
        -e "end tell" > /dev/null
  else
    if $PRINT_WARNING; then
        echo -e "\nWARNING: The OS '$OSTYPE' is not supported yet for creating tabs to setup
        baserow's dev environment, please add support!"
        PRINT_WARNING=false
    fi
    print_manual_instructions "$COMMAND"
  fi
}

show_help() {
    echo """
./dev.sh starts the baserow development environment and by default attempts to
open terminal tabs which are attached to the running dev containers.

Usage: ./dev.sh [optional start dev commands] [optional docker-compose up commands]

The ./dev.sh Commands are:
restart       : Stop the dev environment first before relaunching.
down          : Down the dev environment and don't up after.
kill          : Kill the dev environment and don't up after.
build_only    : Build the dev environment and don't up after.
dont_migrate  : Disable automatic database migration on baserow startup.
dont_sync     : Disable automatic template sync on baserow startup.
dont_attach   : Don't attach to the running dev containers after starting them.
help          : Show this message.
"""
}

dont_attach=false
down=false
kill=false
build=false
run=false
up=true
migrate=true
sync_templates=true
while true; do
case "${1:-noneleft}" in
    dont_migrate)
        echo "./dev.sh: Automatic migration on startup has been disabled."
        shift
        migrate=false
    ;;
    dont_sync)
        echo "./dev.sh: Automatic template syncing on startup has been disabled."
        shift
        sync_templates=false
    ;;
    dont_attach)
        echo "./dev.sh: Configured to not attach to running dev containers."
        shift
        dont_attach=true
    ;;
    restart)
        echo "./dev.sh: Restarting Dev Environment"
        shift
        down=true
        up=true
    ;;
    down)
        echo "./dev.sh: Stopping Dev Environment"
        shift
        up=false
        down=true
    ;;
    kill)
        echo "./dev.sh: Killing Dev Environment"
        shift
        up=false
        kill=true
    ;;
    run)
        echo "./dev.sh: docker-compose running the provided commands"
        shift
        up=false
        dont_attach=true
        run=true
    ;;
    build_only)
        echo "./dev.sh: Only Building Dev Environment (use 'up --build' instead to
        rebuild and up)"
        shift
        build=true
        up=false
    ;;
    help)
        show_help
        exit 0
    ;;
    *)
        break
    ;;
esac
done

CURRENT_UID=$(id -u)
CURRENT_GID=$(id -g)
export CURRENT_UID
export CURRENT_GID


if [[ -z "${MIGRATE_ON_STARTUP:-}" ]]; then
if [ "$migrate" = true ] ; then
export MIGRATE_ON_STARTUP="true"
else
# Because of the defaults set in the docker-compose file we need to explicitly turn
# this off as just not setting it will get the default "true" value.
export MIGRATE_ON_STARTUP="false"
fi
else
  echo "./dev.sh Using the already set value for the env variable MIGRATE_ON_STARTUP = $MIGRATE_ON_STARTUP"
fi

if [[ -z "${SYNC_TEMPLATES_ON_STARTUP:-}" ]]; then
if [ "$sync_templates" = true ] ; then
export SYNC_TEMPLATES_ON_STARTUP="true"
else
# Because of the defaults set in the docker-compose file we need to explicitly turn
# this off as just not setting it will get the default "true" value.
export SYNC_TEMPLATES_ON_STARTUP="false"
fi
else
  echo "./dev.sh Using the already set value for the env variable SYNC_TEMPLATES_ON_STARTUP = $SYNC_TEMPLATES_ON_STARTUP"
fi

if [ "$down" = true ] ; then
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
fi

if [ "$kill" = true ] ; then
docker-compose -f docker-compose.yml -f docker-compose.dev.yml kill
fi

if [ "$build" = true ] ; then
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build "$@"
fi

if [ "$up" = true ] ; then
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d "$@"
fi

if [ "$run" = true ] ; then
docker-compose -f docker-compose.yml -f docker-compose.dev.yml run "$@"
fi

if [ "$dont_attach" != true ] && [ "$up" = true ] ; then
  new_tab "Backend" \
          "docker logs backend && docker attach backend"

  new_tab "Backend celery" \
          "docker logs celery && docker attach celery"

  new_tab "Web frontend" \
          "docker logs web-frontend && docker attach web-frontend"

  new_tab "Web frontend lint" \
          "docker exec -it web-frontend /bin/bash /web-frontend/docker/docker-entrypoint.sh lint-fix"
fi
