# Upgrade from Ubuntu Baserow to Docker Baserow

The [Install on Ubuntu](install-on-ubuntu.md) guide is now deprecated. We are asking
any users who wish to run Baserow on Ubuntu to instead install Docker and use our
official Docker images to run Baserow. This guide explains how to migrate an existing
Baserow Ubuntu install to use our official Docker images.

## Migration Steps

1. Install Docker
```bash
sudo apt-get install docker
```
2. Stop your old Baserow server
```bash
supervisorctl stop all
```
3. Start a new Baserow docker container connected to your existing postgres database.
```bash
# Change http://localhost to https://www.yourdomain.com you wish to host Baserow on a
# domain. 
docker run \
  -d \
  --name baserow \
  -e DOMAIN=http://localhost \
  -e DATABASE_URL=postgresql://baserow:baserow@localhost:5432/baserow \
  -v $(pwd)/baserow_data:/baserow/data \
  -p 80:80 \
  -p 443:443 \
  baserow/baserow:1.8.2
```
4. Check the logs and wait for Baserow to become available

