#!/usr/bin/env bash
set -Eeoux pipefail

DOCKER_USER=${DOCKER_USER:-baserow_docker_user}
# We might be running as a user which already exists in this image. In that situation
# Everything is OK and we should just continue on.
groupadd -g "$GID" baserow_docker_group || exit 0
useradd --shell /bin/bash -u $UID -g "$GID" -o -c "" -m "$DOCKER_USER" -l || exit 0
# Ensure the user can write to /dev/stdout etc.
usermod -a -G tty "$DOCKER_USER"

# Create a separate Caddy user
groupadd caddy
useradd --shell /bin/bash -g caddy -c "" -m caddy -l
# Ensure the user can write to /dev/stdout etc.
usermod -a -G tty caddy

apt-get update
apt-get upgrade -y
DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install --no-install-recommends -y \
make supervisor curl gnupg2 \
libpq-dev \
redis-server \
postgresql postgresql-contrib postgresql-client \
python3 \
ca-certificates \
tini \
gosu \
libnss3-tools # Used by caddy trust below to install certs.

usermod -a -G tty redis
usermod -a -G tty postgres

curl -fsSL https://deb.nodesource.com/setup_12.x | bash -

apt-get install --no-install-recommends -y nodejs
rm -rf /var/cache/apt /var/lib/apt/lists

# Download and install caddy.
curl -o caddy.tar.gz -sL https://github.com/caddyserver/caddy/releases/download/v2.4.6/caddy_2.4.6_linux_amd64.tar.gz
tar -xf caddy.tar.gz
mv caddy /usr/bin/
HOME=~"$DOCKER_USER" caddy trust
rm caddy.tar.gz

# Ensure supervisor logs to stdout
ln -sf /dev/stdout /var/log/supervisor/supervisord.log

# Ensure redis is not running in daemon mode as supervisor will supervise it directly
sed -i 's/daemonize yes/daemonize no/g' /etc/redis/redis.conf
sed -i 's/daemonize no/daemonize no\nbind 127.0.0.1/g' /etc/redis/redis.conf
# Point redis at our data dir
sed -i "s;dir /var/lib/redis;dir $DATA_DIR/redis;g" /etc/redis/redis.conf
# Ensure redis logs to stdout by removing any logfile statements
sed -i '/^logfile/d' /etc/redis/redis.conf
# Sedding changes the owner, change it back.
chown redis:redis /etc/redis/redis.conf

# Setup postgres to point at the DATA_DIR
sed -i "s;/var/lib/postgresql/11/main;$DATA_DIR/postgres;g" /etc/postgresql/11/main/postgresql.conf
chown postgres:postgres /etc/postgresql/11/main/postgresql.conf
