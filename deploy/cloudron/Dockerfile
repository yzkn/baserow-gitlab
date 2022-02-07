ARG FROM_IMAGE=baserow/baserow:1.8.2
FROM $FROM_IMAGE as image_base
FROM cloudron/base:3.0.0@sha256:455c70428723e3a823198c57472785437eb6eab082e79b3ff04ea584faf46e92

ENV DOCKER_USER=cloudron
ENV DATA_DIR=/app/data
ENV TMPDIR=/run/temp

COPY ./deploy/all-in-one/install-docker-dependencies.sh /baserow/install-docker-dependencies.sh
RUN ./baserow/install-docker-dependencies.sh && rm ./baserow/install-docker-dependencies.sh

COPY --chown cloudron:cloudron --from image_base /baserow/ /baserow/
# The copy above will have chowned the supervisor folder to cloudron user when it should
# be root.
RUN chown -R root:root /baserow/supervisor

COPY deploy/cloudron/cloudron_env.sh /baserow/supervisor/env/cloudron_env.sh
COPY deploy/all-in-one/baserow.sh /baserow.sh

ENTRYPOINT ["/baserow.sh"]
CMD ["start"]
