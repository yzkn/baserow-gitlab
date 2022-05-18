#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -eo pipefail
# Enable buildkit for faster builds with better caching.
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1

if [[ -z "$PLUGIN_BUILD_UID" ]]; then
PLUGIN_BUILD_UID=$(id -u)
fi
export PLUGIN_BUILD_UID

if [[ -z "$PLUGIN_BUILD_GID" ]]; then
PLUGIN_BUILD_GID=$(id -g)
fi
export PLUGIN_BUILD_GID

docker-compose -f docker-compose."$1".yml "${@:2}"