#!/usr/bin/env bash
set -Eeo pipefail

PREFIX=$1
shift


# Force stdout to flush immediately
exec "$@" |& sed -u "s/^/[$PREFIX:$(date +%Y-%m-%d\ %T)] /g"
