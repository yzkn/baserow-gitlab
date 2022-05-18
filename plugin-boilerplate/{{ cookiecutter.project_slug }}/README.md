# {{ cookiecutter.project_name }}

## Baserow Plugins

A Baserow plugin can be used to extend or change the functionality of Baserow. 
Specifically a plugin is a folder with a `backend` and/or `web-frontend` folder. 

## How to run {{ cookiecutter.project_name }} using Docker-compose

A number of different example docker-compose files are provided in this folder:

> It is recommended to use build kit with these compose files, you can do this by
> running:
> ```bash
> export COMPOSE_DOCKER_CLI_BUILD=1
> export DOCKER_BUILDKIT=1
> ```

1. `docker-compose.yml` - This is the simplest compose file that will run the your 
   plugin installed into a single container, use `docker-compose up`.
2. `docker-compose.caddy.yml` - This is a more complex compose file which runs each of
   the Baserow services with your plugin installed in separate containers all behind a
   Caddy reverse proxy.
    1. `docker-compose -f docker-compose.caddy.yml up -d --build`
3. `docker-compose.dev.yml` - This is a development compose file which runs service in 
   a separate container like the `.caddy.yml` above. The images used will be
   the development variants which have dev dependencies installed. Additionally, it will
   mount in the local source code into the containers so for hot code reloading. To
   ensure the mounting of your local code into the contains works correctly make sure
   you run with the following two environment variables set to your uid and gid:
    1. `PLUGIN_BUILD_UID=$(id -u) PLUGIN_BUILD_GID=$(id -g) docker-compose -f docker-compose.dev.yml up -d --build`

## Missing features TODO

1. A templated setup guide in the generated folder itself.
2. Example tests for web-frontend and backend.
3. An equivalent dev.sh
4. Setup instructions for IDEs (vs-code/intellij)
5. Example Gitlab/Github CI integration + instructions to publish plugin to Dockerhub.
