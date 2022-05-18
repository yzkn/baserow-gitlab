# Introduction

Baserow plugins let you easily add extra features or change existing ones using our
flexible architecture. They are only available for self-hosted installations currently
and are **highly experimental** and subject to change.

1. **You should always make backups of your Baserow data before installing and using any
   plugin.**
2. **You should only ever install plugins from a trusted source.**

## Plugin Installation

Before we begin, Baserow plugins are in **alpha** and so there are important things to
know about:

* A Baserow plugin when installed has full access to your data and can execute any
  arbitrary code it likes. Baserow does not sandbox or perform any security checks on
  plugins.
* Baserow does not yet verify or guarantee the safety of any plugins and does not take
  responsibility for any damage or loss caused by installing or using any plugins.
* They are only for advanced users who are comfortable with Docker, volumes, containers
  and the command line.
* There are a number of missing plugin features, e.g. there is no UI for inspecting
  installed plugins and everything is done via the command line.

There are two main ways to install a plugin:

### By building your own all-in-one image

The easiest, fastest and most reliable way to install a Baserow plugin currently is to
build your own image based off of the Baserow all-in-one image:

1. Ensure you have `docker` installed and it is upto date.
2. Create your own `Dockerfile` which will customize the normal Baserow image and
   install your own plugins, all the various ways of installing a plugin are shown
   in the example Dockerfile below:

```dockerfile
FROM baserow/baserow:1.10.0

# You can install a plugin found in a git repo:
RUN /baserow/plugins/install_plugin.sh \
    --git https://gitlab.com/example/example_baserow_plugin.git
    
# Or you can download a tar.gz directly from an url 
RUN /baserow/plugins/install_plugin.sh \
    --url https://example.com/plugin.tar.gz
    
# Or you can install the plugin from a local folder by copying it into the image and \
# then installing using --folder
COPY ./some_local_dir_containing_your_plugin/ /baserow/plugins/your_plugin/
RUN /baserow/plugins/install_plugin.sh \
    --folder /baserow/plugins/your_plugin/

# The --hash flag below will make the install_plugin.sh script check that the 
# plugin exactly matches the provided hash. 
#
# We recommend you provide this flag to make sure the downloaded plugin has not
# been malciously modified or changed since the last time you installed.
#
# To get the hash of a plugin simply run the docker build with a nonsense --hash
# value. Then the build will fail and `install_plugin.sh` will print the hash of the 
# downloaded plugin. Then you can replace your nonsense --hash value with the printed
# one and build again.
RUN /baserow/plugins/install_plugin.sh \
    --git https://gitlab.com/example/example_baserow_plugin.git \
    --hash hash_of_plugin_2
```

3. Now build your custom Baserow with the plugin installed by running:
   `docker build -t my-customized-baserow:1.10.0 .`
4. Finally, you can run your new customized image just like the normal Baserow image:
   `docker run -p 80:80 -v baserow_data:/baserow/data my-customized-baserow:1.10.0`

### Installing in an existing Baserow all-in-one container

This method installs the plugin into a running container, and it's data volume.

1. It is highly recommended that you backup your data before installing a plugin, see
   the [Docker install guide backup section](../installation/install-with-docker.md)
   for more details on how to do this.
2. Stop your Baserow server first - `docker stop baserow`

```bash
docker run \
  -v baserow_data:/baserow/data \ 
  baserow:1.10.0 install-plugin \
  --git https://gitlab.com/example/example_baserow_plugin.git \
  --hash hash_of_plugin_1
```

3. Now start your Baserow server again - `docker start baserow`.

### Using an environment variable

You can use the `BASEROW_PLUGIN_GIT_REPOS` or `BASEROW_PLUGIN_URLS` env variables when
using the
`baserow/baserow` image:
1. The `BASEROW_PLUGIN_GIT_REPOS` should be a list of https git repo urls which will
   be used to download and install plugins on startup.
2. The `BASEROW_PLUGIN_URLS` should be a list of urls which will
   be used to download and install plugins on startup.

For example you could start a new Baserow container with plugins installed by running:

```bash
docker run \
  -v baserow_data:/baserow/data \ 
  # ...  All your normal launch args go here
  -e BASEROW_PLUGIN_GIT_REPOS=https://example.com/example/plugin1.git,https://example.com/example/plugin2.git
  baserow:1.10.0
```

These variables will only trigger and installation when found on startup of the 
container. To uninstall a plugin you must still manually follow the instructions below. 

### Caveats with installing into an existing container

If you ever delete the container you've installed plugins into at runtime and re-create
it, the new container is initially created from the `baserow/baserow:1.10.0` image which
does not have any plugins installed.

However, when a plugin is installed at runtime or build time it is stored in the
`/baserow/data/plugins` container location which should be mounted inside a volume. On
startup if a plugin is found in this directory which has not yet been installed into the
current container it will be re-installed.

As long as you re-use the same data volume which was being used previously when you
installed a plugin at runtime and the plugin itself stores all of it's data in the
postgres database and/or the `/baserow/data` directory you won't lose any data or
plugins when re-creating containers. The only affect is on initial container startup you
might see the plugins re-installing themselves when you re-create the container from
scratch.

### Installing into standalone Baserow service images

Baserow also provides `baserow/backend:1.10.0` and `baserow/web-frontend:1.10.0` images
which only run the respective backend/celery/web-frontend services. These images are
used for more advanced self-hosted deployments like a multi-service docker-compose, k8s
etc.

These images also ship with the following scripts available to install/manage plugins:

1. `/baserow/plugins/install_plugin.sh`
2. `/baserow/plugins/uninstall_plugin.sh`
3. `/baserow/plugins/list_plugins.sh`

You can use these scripts exactly as you would in the sections above to install a plugin
in a Dockerfile or at runtime. The scripts will automatically detect if they are running
in a `backend` only or `web-frontend` only image and only install the respective
plugin `backend` or `web-frontend` module.

The [plugin boilerplate](./boilerplate.md) provides examples of doing this in the
`backend.Dockerfile` and `web-frontend.Dockerfile` images.

## Uninstalling a plugin

**WARNING:** This will remove the plugin from your Baserow installation and delete all
associated data permanently.

1. It is highly recommended that you backup your data before uninstalling a plugin, see
   the
   [Docker install guide backup section](../installation/install-with-docker.md)
   for more details on how to do this.
2. Stop your Baserow server first - `docker stop baserow`
3. `docker run -v baserow_data:/baserow/data baserow:1.10.0 uninstall-plugin plugin_name`
4. Now the plugin has uninstalled itself and all associated data has been removed. If
   you are using your own custom-built image if Baserow with the plugin installed you
   must now:
    1. Edit the `Dockerfile` and remove the plugin.
    2. Rebuild your image - `docker build -t my-customized-baserow:1.10.0 .`
    3. Remove the old container using the old image - `docker rm baserow`
    4. Run your new image with the plugin removed
        - `docker run -p 80:80 -v baserow_data:/baserow/data my-customized-baserow:1.10.0`
    5. If you fail to do this if you ever recreate the container, your custom image
       still has the plugin installed and the new container will start up again with the
       plugin installed.

## Checking which plugins are already installed

Use the `list-plugins` command or built in `/baserow/plugins/list_plugins.sh` script to
check what plugins are currently installed.

```bash
docker run \
  --rm \
  -v baserow_data:/baserow/data \ 
  baserow:1.10.0 list-plugins 

# or on a running container

docker exec baserow /baserow/plugins/list_plugin.sh
```

## Creating a plugin

We highly recommend using the [plugin boilerplate](./boilerplate.md). You can easily
create a simple starting plugin using our cookiecutter template. All the python modules
and javascript files are already in place, and it comes with a docker development
environment.

### Plugin Architecture

Baserow has two main services, a Django `backend` API server and a Nuxt frontend
`web-frontend` server. A Baserow plugin can contain a python module and/or a node
package to plugin into either or both of these Baserow services.

Since the `backend` service is built with Django, a `backend` plugin is simply a
Django [app](https://docs.djangoproject.com/en/3.4/ref/applications/). Nuxt.js has a
similar approach which can be used, but in Nuxt, plugins are called
[modules](https://nuxtjs.org/guide/modules).

### Plugin Installation API

> The current Baserow Plugin API Version is `0.0.1-alpha`.

All the Baserow official images ship with the following bash scripts which are used to
install plugins. They can be used either in a Dockerfile at build time to install a
plugin or to install a plugin into an existing Baserow container at runtime.

1. `/baserow/plugins/install_plugin.sh`
2. `/baserow/plugins/uninstall_plugin.sh`
3. `/baserow/plugins/list_plugins.sh`

These scripts expect a Baserow plugin to follow the conventions described below.

#### Plugin File Structure

The `install_plugin.sh/uninstall_plugin.sh` scripts expect your plugin to have a
specific structure as follows:

```
├── plugin_name
│  ├── baserow_plugin_info.json
│  ├── backend/ (Optional backend python plugin )
│  │  ├── setup.py
│  │  ├── build.sh (Called when installing the plugin in a Dockerfile/container)
│  │  ├── runtime_setup.sh (Called on first runtime startup of the plugin)
│  │  ├── uninstall.sh (Called when uninstalling the plugin in a container)
│  │  ├── src/plugin_name/src/config/settings/settings.py (Optional Django setting file)
│  ├── web-frontend/ (Optional web-frontend node plugin )
│  │  ├── package.json
│  │  ├── build.sh (Called when installing the plugin in a Dockerfile/container)
│  │  ├── runtime_setup.sh (Called on first runtime startup of the plugin)
│  │  ├── uninstall.sh (Called when uninstalling the plugin in a container)
│  │  ├── modules/plugin_name/module.js (Your plugins module file)
```

#### The plugin info file.

The `baserow_plugin_info.json` file is a json file containing metadata about your plugin
and should contain the following:

```json
{
  "name": "",
  "version": "",
  "supported_baserow_versions": "1.11.0>=",
  "plugin_api_version": "0.0.1-alpha",
  "description": "",
  "author": "",
  "author_url": "",
  "url": "",
  "license": "",
  "contact": ""
}
```

#### Expected plugin structure when installing via a .tar.gz download

When using `install_plugin.sh --url URL_TO_PLUGIN_TAR_GZ` the plugin archive should
contain a single `plugins` folder, inside which there should a single plugin folder
following the structure above which has the same name as your plugin. By default,
the [plugin boilerplate](./boilerplate.md) generates a repository with this structure.
For example a conforming tar.gz archive should contain something like:

```
├── plugins/ 
│  ├── plugin_name/
│  │  ├── baserow_plugin_info.json 
│  │  ├── backend/
│  │  ├── web-frontend/
```

## Writing a Plugin

Now you have created a plugin, lets go into more detail of how to actually extend and
customize Baserow using your plugin.

First you should read the following documentation for a basic introduction to Baserow's
technical architecture:

1. [Baserow Technical Introduction](../technical/introduction.md)
2. [Database Plugin](../technical/database-plugin.md)

### Writing a Backend Plugin

#### Adding Python Requirements

Your backend plugin is just a normal python module which will be installed into the
Baserow virtual environment using `pip` by `install_plugin.sh`. If using the plugin
boilerplate you can add any python requirements to the pip requirements file found
at `backend/requirements/base.txt`.

#### As a Django App

When the Baserow backend Django service starts up it looks for any plugins in the plugin
directory which have a `backend` sub-folder. If it finds any it assumes
the `backend/src/plugin_name/`
sub folder contains a Django App and adds it to the `INSTALLED_APPS`. This means that
your backend plugin must be a Django app whose name exactly matches the name of the
plugin folder.

In your plugin's Django app you can do anything that you normally can do with a Django
app such as having migrations, using the `ready()` method to do startup configuration
etc.

#### Backend Registries

Baserow has a number of registries which are used to dynamically configure Baserow. For
example the `field_type_registry` contains various implementations of the `FieldType`
class.

Each registry contains various implementations of a particular "interface" class. A
registry in Baserow is simply a singleton dictionary populated by apps in their `ready`
method. Then Baserow's various API endpoints will use these registries at runtime.

So in your plugin's Django Apps `ready` method is where you should import any relevant
registries and register your own implementations of field types.

For example, the `plugin_registry` is used to register implementations of the
`baserow.core.registries.Plugin` interface. You can create your own class which
implements this base class and register it with the `plugin_registry` by:

```python
from baserow.core.registries import plugin_registry
from django.apps import AppConfig


class PluginNameConfig(AppConfig):
    name = "my_baserow_plugin"

    def ready(self):
        from .plugins import PluginNamePlugin

        plugin_registry.register(PluginNamePlugin())
```

You can see all the different things you can dynamically register into Baserow with your
plugin by searching the Baserow codebase and inspecting the `registry.py` and
`registries.py` files.

### Writing a Web Frontend Plugin

#### Adding Node Requirements

Your web-frontend plugin is just a normal node package which will be installed into
Baserow's node_modules using `yarn` by `install_plugin.sh`. You can add any extra
frontend requires to your `web-frontend/package.json`.

#### Web-frontend Registries

The Baserow web-frontend nuxt app also follows the registry pattern that the backend
has. This means it has an equivalent frontend registry for most backend registries where
it makes sense. So if you were to registry a new field type in the backend registry then
also make sure to registry a new field type in the frontend registry also.

### Further Reading

Check out the following guides in the plugin section which go into more specifics on say
creating a new field type:

1. [Application Type Guide](./application-type.md)
1. [Field Type Guide](./field-type.md)
1. [Field Converter Guide](./field-converter.md)
1. [View Type Guide](./view-type.md)
1. [View Filter Type Guide](./view-filter-type.md)
