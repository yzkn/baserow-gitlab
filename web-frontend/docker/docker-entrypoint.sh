#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

PORT="${PORT:-3000}"

show_help() {
# If you change this please update ./docs/reference/baserow-docker-api.md
    echo """
Usage: docker run [-T] baserow_web-frontend[_dev] COMMAND
Commands
dev      : Start a normal nuxt development server
local    : Start a non-dev prod ready nuxt server
lint     : Run all the linting
lint-fix : Run eslint fix
stylelint: Run stylelint
eslint   : Run eslint
test     : Run jest tests
ci-test  : Run ci tests with reporting
bash     : Start a bash shell
exec     : Exec a command directly
help     : Show this message
"""
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
    nuxt-dev)
        attachable_exec yarn run dev
    ;;
    nuxt)
      exec ./node_modules/.bin/nuxt --hostname 127.0.0.1 --port "$PORT" "${@:2}"
    ;;
    nuxt-local)
      exec ./node_modules/.bin/nuxt --hostname 127.0.0.1 --port "$PORT" --config-file ./config/nuxt.config.local.js "${@:2}"
    ;;
    lint)
      exec make lint-javascript
    ;;
    lint-fix)
      attachable_exec yarn run eslint --fix
    ;;
    eslint)
      exec make eslint
    ;;
    stylelint)
      exec make eslint
    ;;
    test)
      exec make jest
    ;;
    ci-test)
      exec make ci-test-javascript
    ;;
    exec)
        exec "${@:2}"
    ;;
    bash)
      exec /bin/bash "${@:2}"
    ;;
    *)
      echo "${@:2}"
      show_help
      exit 1
    ;;
esac
