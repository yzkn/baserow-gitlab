# Boilerplate

With the plugin boilerplate you can easily create a new plugin and setup a docker
development environment that installs Baserow as a dependency. It includes linters and
it can easily be installed via cookiecutter.

> The structure used for Baserow plugins is not yet finalized and might change to
> support installation of plugins via a market-place available in Baserow.

## Creating plugin

Before the cookiecutter plugin boilerplate template can be used you first need to clone
the Baserow repository and install cookiecutter. In this example I will assume you are
working in an empty directory at `~/baserow` and that you have installed python and pip.

```
$ cd ~/baserow
$ pip install cookiecutter
$ git clone --branch master https://gitlab.com/bramw/baserow.git
Cloning into 'baserow'...
```

Inside the cloned repository lives the plugin boilerplate. By executing the following
command we are going to create a new plugin. For example purposes we will name this
plugin "My Baserow Plugin". You can choose how you want to name your plugin via the
cookiecutter input prompts.

> The python module depends on the given project name. If we for example go with
> "My Baserow Plugin" the Django app name will be my_baserow_plugin and the Nuxt module
> name will be my-baserow-plugin.

```
$ cookiecutter baserow/plugin-boilerplate
project_name [My Baserow Plugin]: 
project_slug [my-baserow-plugin]: 
project_module [my_baserow_plugin]:
```

If you do not see any errors it means that your plugin has been created.

## Starting the development environment

Now to start your development environment please run the following command:

```bash
$ cd my-baserow-plugin
$ PLUGIN_BUILD_UID=$(id -u) PLUGIN_BUILD_GID=$(id -g) docker-compose -f docker-compose.dev.yml up -d --build
$ docker-compose -f docker-compose.dev.yml logs -f
...
# Please wait whilst Baserow syncs templates for the first time on startup, this might
# take some time. 

```

The development environment is now running and can be accessed at http://localhost:3000.

## First changes

The most important part inside the my-baserow-plugin folder is the
plugins/my_baserow_plugin folder. Here you will find all the code of your plugin. For
example purposes we are going to add a simple endpoint which always returns the same
response, and we are going to show this text on a page in the web frontend.

### Backend changes

We want to expose an endpoint on the following url
http://localhost:8000/api/my-baserow-plugin/example/ that returns a JSON response
containing a title and some content. Create/Modify the following files:

First create `plugins/my_baserow_plugin/backend/src/my_baserow_plugin/api/views.py`

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


class ExampleView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response({
            'title': 'Example title',
            'content': 'Example text'
        })
```

Then modify `plugins/my_baserow_plugin/backend/src/my_baserow_plugin/api/urls.py`

```python
from django.urls import re_path

from .views import ExampleView

app_name = 'my_baserow_plugin.api'
urlpatterns = [
    re_path(r'example/$', ExampleView.as_view(), name='example'),
]
```

With these change you should be able to visit
the [http://localhost:8000/api/my_baserow_plugin/example/](http://localhost:8000/api/my_baserow_plugin/example/)
endpoint which should return the desired content.

### Web frontend changes

Now that we have our endpoint we want to show the response on a page in the
web-frontend. Add/modify the following code.

Modify `plugins/my_baserow_plugin/web-frontend/modules/my-baserow-plugin/routes.js`

```javascript
import path from 'path'

export const routes = [
    {
        name: 'example',
        path: '/example',
        component: path.resolve(__dirname, 'pages/example.vue'),
    },
]
```

Add `plugins/my_baserow_plugin/web-frontend/modules/my-baserow-plugin/pages/example.vue`

```vue

<template>
  <div>
    {{ content }}
  </div>
</template>

<script>
export default {
  async asyncData({app}) {
    // TODO Make sure you change this url prefix to the underscore separated and 
    // lowercase name of your plugin.
    const response = await app.$client.get('my_baserow_plugin/example/')
    return response.data
  },
  head() {
    return {
      title: this.title,
    }
  },
}
</script>

```

Now you will need to restart the Nuxt development server because the routes have changes
and they are loaded by the module.js.
Run `docker-compose -f docker-compose.dev.yml restart web-frontend` to do this.

If you now visit http://localhost:3000/example in your browser you should see a page
containing the title and content defined in the endpoint.

You should now have a basic idea on how to make some changes to Baserow via the plugin
boilerplate. The changes we have discussed here are of course for example purposes and
are only for giving you an idea about how it works.

## Linters

The linters on the web-frontend side should run automatically when the development
server is running. After you have started the dev environment and the containers are all
running you can run the following commands to run the linters.

* `docker-compose -f docker-compose.dev.yml exec web-frontend /bin/bash`
    * You are now in a shell inside the web-frontend dev container. 
    * `cd /baserow/plugins/my_baserow_plugin/web-frontend/`
    * Now you can run any commands you would like:
      * `yarn run eslint --fix`
      * `yarn run styleint `
      * `yarn add your_dependency`
* `docker-compose -f docker-compose.dev.yml exec backend /bin/bash`
  * You are now in a shell inside the backend dev container.
  * `cd /baserow/plugins/my_baserow_plugin/backend/`
  * `source /baserow/venv/bin/activate`
  * Now you can run any commands you would like:
    * `pytest`
    * `flake8`
    * `black .`

## Next Steps

The [Plugin Introduction](./introduction.md) contains further info on plugins. Also see 
the README.md in the root of your plugin folder.
