## Baserow is an open source no-code database tool and Airtable alternative. 

Create your own online database without technical experience. Our user-friendly no-code 
tool gives you the powers of a developer without leaving your browser.

* A spreadsheet database hybrid combining ease of use and powerful data organization.
* Can be self-hosted or used instantly on https://baserow.io.
* Open source under the (https://choosealicense.com/licenses/mit/)
  allowing commercial and private use.

![Baserow screenshot](docs/assets/screenshot.png "Baserow screenshot")

Join our forum on
https://community.baserow.io/ or on Gitter via
https://gitter.im/bramw-baserow/community.

**We're hiring** remote developers! More information at 
https://baserow.io/jobs/experienced-full-stack-developer.

## Installation

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/bram2w/baserow/tree/master)

### Docker

```bash
docker run -v baserow_data:/baserow/data -p 80:80 -p 443:443 baserow/baserow:1.8.2

# Set the DOMAIN env variable to easily host Baserow on your domain with auto HTTPS 
# thanks to Caddy:
docker run -e DOMAIN=https://www.yourdomain.com -v baserow_data:/baserow/data -p 80:80 -p 443:443 baserow/baserow:1.8.2
```

See our [Install using Docker](docs/installation/install-using-docker.md) guide
for full instructions and further customization options.

### Docker-compose

```
$ git clone --branch master https://gitlab.com/bramw/baserow.git
$ cd baserow
$ docker-compose up -d
$ docker-compose ps
$ docker-compose logs
```

See our [Install using Docker-Compose](docs/installation/install-using-docker-compose.md) 
guide for full instructions and further customization options.

### Other self-hosting solutions

* [**Heroku**: Easily install and scale up on Heroku by using the template.](docs/installation/install-on-heroku.md)
* [**Cloudron**: Install and update Baserow on your own Cloudron server.](docs/installation/install-on-cloudron.md)


## Development environment

If you want to contribute to Baserow you can setup a development environment with
hot reloading and debug logging enabled like so:

```
$ git clone https://gitlab.com/bramw/baserow.git
$ cd baserow
$ # Then use ./dev.sh script runs our docker-compose dev files with some environment 
$ # setup
$ ./dev.sh --build
```

The Baserow development environment is now running. Visit http://localhost:3000 in your
browser and you should see a working version in development mode.

More detailed instructions and more information about the development environment can 
be found [here](./docs/development/development-environment.md) or at 
https://baserow.io/docs/development/development-environment.

## Plugin development

Because of the modular architecture of Baserow it is possible to create plugins. Make 
your own fields, views, applications, pages or endpoints. We also have a plugin 
boilerplate to get you started right away. More information can be found in the 
[plugin introduction](./docs/plugins/introduction.md) and in the 
[plugin boilerplate docs](./docs/plugins/boilerplate.md).

## Official documentation

The official documentation can be found on the website at https://baserow.io/docs/index
or [here](./docs/index.md) inside the repository. The API docs can be found here at 
https://api.baserow.io/api/redoc/ or if you are looking for the OpenAPI schema here
https://api.baserow.io/api/schema.json.

## Become a sponsor

If you would like to get new features faster, then you might want to consider becoming
a sponsor. By becoming a sponsor we can spend more time on Baserow which means faster
development.

[Become a GitHub Sponsor](https://github.com/sponsors/bram2w)

## Meta

Created by Baserow B.V. - bram@baserow.io.

Distributes under the MIT license. See `LICENSE` for more information.

Version: 1.8.2

The official repository can be found at https://gitlab.com/bramw/baserow.

The changelog can be found [here](./changelog.md).

Become a GitHub Sponsor [here](https://github.com/sponsors/bram2w).

Community chat via https://gitter.im/bramw-baserow/community.
