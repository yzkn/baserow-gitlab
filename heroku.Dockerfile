ARG FROM_IMAGE=baserow/baserow:1.8.2
FROM $FROM_IMAGE as image_base

COPY deploy/heroku/heroku_env.sh /baserow/supervisor/env/heroku_env.sh
