# TODO before merge switch back to proper dockerhub image
FROM registry.gitlab.com/bramw/baserow/ci/web-frontend:ci-latest-432-update-plugin-boilterplate-and-docs-to-match-new-docker-usage

USER root

ARG PLUGIN_BUILD_UID
ENV PLUGIN_BUILD_UID=${PLUGIN_BUILD_UID:-9999}
ARG PLUGIN_BUILD_GID
ENV PLUGIN_BUILD_GID=${PLUGIN_BUILD_GID:-9999}

# If we aren't building as the same user that owns all the files in the base
# image/installed plugins we need to chown everything first.
RUN [ "/bin/bash", "-c", "if [[ $PLUGIN_BUILD_UID != '9999' || $PLUGIN_BUILD_GID != '9999' ]] ; then chown -R $PLUGIN_BUILD_UID:$PLUGIN_BUILD_GID /baserow/; fi" ]

COPY --chown=$PLUGIN_BUILD_UID:$PLUGIN_BUILD_GID ./plugins/{{ cookiecutter.project_module }}/ /baserow/plugins/{{ cookiecutter.project_module }}/
RUN /baserow/plugins/install_plugin.sh --folder /baserow/plugins/{{ cookiecutter.project_module }} --dev

USER $PLUGIN_BUILD_UID:$PLUGIN_BUILD_GID
CMD ["nuxt-dev"]
