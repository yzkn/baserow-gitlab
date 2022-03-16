# VSCode Setup

This guide walks you through a first time VScode setup for Baserow for developers. It
will ensure you can run and debug all tests and also enable all the relevant linters and
automatic style fixers to make your life as easy as possible.

> This guide assumes you have a basic understanding of git, python, virtualenvs,
> postgres and command line tools.

1. First checkout a fresh copy of Baserow: `git clone git@gitlab.com:bramw/baserow.git`
1. `cd baserow`
1. `./config/vscode/apply_standard_baserow_vscode_config.sh`
    1. Type `Y` and hit enter to apply the standard Baserow config
1. Open VSCode and on the "Welcome to VSCode" screen click the "Open" button
   and open the baserow folder you cloned above.
1. Make sure you have installed / enabled the Python VSCode plugin.
1. Now we will create python virtualenv and configure VSCode to use it to run tests
   and linters:
    1. Choose a location for your virtualenv, it is recommended to store it separately
       from the baserow source-code folder so VSCode does not search nor index it.
    2. Create the virtualenv: `python3 -m venv venv` or `virtualenv -p python venv`
    3. Activate the virtualenv: `source venv/bin/activate` (will differ depending on
       your shell)
    4. Run `which pip` and ensure the output of this command is now pointing into the
       bin in your new virtualenv
    5. Change to the Baserow source directory: `cd path/to/your/baserow`
    6. Install all the Baserow python requirements into your virtualenv:
       `pip install -r backend/requirements/dev.txt -r backend/requirements/base.txt`
    7. Now back in VSCode, press F4 or right-click on the top level baserow folder and
       select `module settings`:
        1. Make sure the `backend` module SDK is set to the python virtualenv you just
           made.
        1. There will most likely be an existing `Python 3.8 (baserow)` virtualenv SDK
           which is red. Delete this first.
        1. Then you will most likely need to add it as a new SDK by navigating to
            1. Ctrl + Shift + P
            1. Python: select interpreter
            1. Find and select your virtualenvs `bin/python` executable
1. Install and get a postgresql database running locally:
    1. [https://www.postgresql.org/docs/11/tutorial-install.html](https://www.postgresql.org/docs/11/tutorial-install.html)
    2. Change the default postgres port otherwise it will clash when running with
       Baserow (the default VSCode config in the repo assumes your testing db is
       running on 5430)
        1. [https://stackoverflow.com/questions/187438/change-pgsql-port](https://stackoverflow.com/questions/187438/change-pgsql-port)
    3. Create a baserow user called `baserow` with the password `baserow` and give them
       permission to create databases
        1. [https://medium.com/coding-blocks/creating-user-database-and-adding-access-on-postgresql-8bfcd2f4a91e](https://medium.com/coding-blocks/creating-user-database-and-adding-access-on-postgresql-8bfcd2f4a91e)

            ```sql
            CREATE USER baserow WITH ENCRYPTED PASSWORD 'baserow';
            ALTER USER baserow CREATEDB;
            ```
    4. You might also have to `pip install psycopg2-binary` or
       `sudo apt install postgresql-devel`
1. Now you should be able to run the backend python tests from the testing menu, try
   run `backend/tests/baserow/core/test_core_models.py` for instance.
1. Now lets set up your frontend dev by changing directory to `baserow/web-frontend`
1. Install [nvm](https://github.com/nvm-sh/nvm) to install the correct version of `node`.
   In `launch.json` the `runtimeVersion` is set to `v12.22.2`, so install this specific
   version using the command: `nvm install v12.22.2`. Then enabled it with the command: `nvm use v12.22.2`
1. Now run `yarn install` to install dependencies.
1. Select "Trust Project" if you see an VSCode popup after running yarn install
1. Confirm you can run a web-frontend unit test from vscode

# Recommended Plugins

You can use the VSC Export & Import to install what is inside `config/vscode/vsc-extensions.txt`.
Otherwise, you can manually install:

1. Python
1. Vetur
1. Eslint