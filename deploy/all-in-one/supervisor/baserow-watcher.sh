#!/usr/bin/env bash
set -Eeo pipefail

baserow_ready() {
    curlf() {
      OUTPUT_FILE=$(mktemp)
      HTTP_CODE=$(curl --silent --output "$OUTPUT_FILE" --write-out "%{http_code}" "$@")
      if [[ ${HTTP_CODE} -lt 200 || ${HTTP_CODE} -gt 299 ]] ; then
        >&2 cat "$OUTPUT_FILE"
        return 22
      fi
      rm "$OUTPUT_FILE"
      return 0
    }

    if curlf "http://localhost:3000/_health/" && curlf "http://localhost:8000/_health/"; then
      return 0
    else
      return 1
    fi
}

wait_for_baserow() {
  until baserow_ready; do
    echo 'Waiting for Baserow to become available...'
    sleep 1
  done
  echo "======================================================================="
  echo -e "\e[32mBaserow is now available at ${DOMAIN:-http://localhost}\e[0m"
  echo "======================================================================="
  unhealthy=false
  while true
  do
    sleep 10
    if ! baserow_ready; then
      echo -e "\e[32mWARNING: Baserow has become unhealthy.\e[0m"
      unhealthy=true
    elif [ "$unhealthy" = true ]; then
      echo -e "\e[33mBaserow has become healthy.\e[0m"
      unhealthy=false
    fi
  done
}

wait_for_baserow
