ARG FROM_BACKEND_IMAGE=baserow_backend
ARG FROM_WEBFRONTEND_IMAGE=baserow_web-frontend
FROM $FROM_BACKEND_IMAGE as backend_image_base
FROM $FROM_WEBFRONTEND_IMAGE as web_frontend_image_base
FROM debian:buster-slim as base

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG UID
ENV UID=${UID:-9999}
ARG GID
ENV GID=${GID:-9999}

ENV DATA_DIR=/baserow/data

COPY ./deploy/all-in-one/install-docker-dependencies.sh /baserow/install-docker-dependencies.sh
RUN ./baserow/install-docker-dependencies.sh && rm ./baserow/install-docker-dependencies.sh

COPY --chown=$UID:$GID deploy/all-in-one/Caddyfile /baserow/caddy/Caddyfile

# We have to explicitly copy the node modules and .nuxt build as otherwise the
# .dockerignore will exclude them.
COPY --chown=$UID:$GID --from=web_frontend_image_base /baserow/web-frontend/node_modules/ /baserow/web-frontend/node_modules/
COPY --chown=$UID:$GID --from=web_frontend_image_base /baserow/web-frontend/.nuxt/ /baserow/web-frontend/.nuxt/
COPY --chown=$UID:$GID --from=web_frontend_image_base /baserow/ /baserow/
COPY --chown=$UID:$GID --from=backend_image_base /baserow/ /baserow/


COPY deploy/all-in-one/supervisor/ /baserow/supervisor
COPY deploy/all-in-one/baserow.sh /baserow.sh


ENTRYPOINT ["/baserow.sh"]
CMD ["start"]
