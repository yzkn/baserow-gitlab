#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

show_help(){
    echo """
Usage: install_plugin.sh [-d] [-f <plugin folder>]
  -f, --folder <plugin folder>        The folder where the plugin to install is located.
  -g, --git <https git repo url>      An url to a https git repo containing the plugin to install.
  -u, --url <plugin url>              An url to a .tar.gz file containing the plugin to install.
      --hash <plugin hash>            The hash of the plugin which will be checked against the loaded plugin to make sure it is genuine.
  -d, --dev                           Install the plugin for development.
  -r, --runtime                       If provided any runtime plugin setup scripts will be run if found. Should never be set if being called from a Dockerfile.
  -h, --help                          Show this help message and exit.

A Baserow plugin is a folder named after the plugin, containing one or both of the
following sub-folders:
  - a 'backend' folder, containing the plugin's backend code. This must be a valid Python
    package.
    - If a 'backend/build.sh' script exists this will be executed to perform any
      additional plugin installation tasks.
  - a 'web-frontend' folder, containing the plugin's backend code. This must be a valid
    node package.
    - If a 'web-frontend/build.sh' script exists this will be executed to perform any
      additional plugin installation tasks.
"""
}

# First parse the args using getopt
VALID_ARGS=$(getopt -o u:dhfr:g: --long hash:,url:,git:,help,dev,folder,runtime: -- "$@")
if [[ $? -ne 0 ]]; then
    echo "ERROR: Incorrect options provided."
    show_help
    exit 1;
fi
eval set -- "$VALID_ARGS"

if [[ "$*" == "--" ]]; then
    echo "ERROR: No arguments provided."
    show_help
    exit 1;
fi

BASEROW_PLUGIN_DIR=${BASEROW_PLUGIN_DIR:-/baserow/plugins}

# Next loop over the user provided args and set flags accordingly.
dev=false
url=
folder=
hash=
git=
exclusive_flag_count=0
runtime=
# shellcheck disable=SC2078
while [ : ]; do
  case "$1" in
    -d | --dev)
        echo "Installing plugin for development..."
        dev=true
        shift
        ;;
    -f | --folder)
        folder="$2"
        shift 2
        exclusive_flag_count=$((exclusive_flag_count+1))
        ;;
    --hash)
        hash="$2"
        shift 2
        ;;
    -u | --url)
        url="$2"
        shift 2
        exclusive_flag_count=$((exclusive_flag_count+1))
        ;;
    -g | --git)
        git="$2"
        shift 2
        exclusive_flag_count=$((exclusive_flag_count+1))
        ;;
    -r | --runtime)
        runtime="true"
        ;;
   -h | --help)
        show_help
        exit 0;
        ;;
    --)
        shift
        break
        ;;
  esac
done

if [[ "$exclusive_flag_count" -eq "0" ]]; then
    echo "ERROR: You must provide one of the following flags: --folder, --url or --git"
    show_help
    exit 1;
fi

if [[ "$exclusive_flag_count" -gt "1" ]]; then
    echo "ERROR: You must provide only one of the following flags: --folder, --url or --git"
    show_help
    exit 1;
fi

# --git was provided, download the plugin using git..
if [[ -n "$git" ]]; then
    echo "Downloading plugin and extracting plugin from git repo at $git..."
    temp_work_dir=$(mktemp -d)
    cd $temp_work_dir
    git clone "$git" .

    dirs=("$temp_work_dir"/plugins/*/)
    num_dirs=${#dirs[@]}
    if [[ "$num_dirs" -ne 1 ]]; then
        echo "ERROR: This git repo does not look like a Baserow plugin. The plugins/ subdirectory in the repo must contain exactly one sub-directory."
        exit 1;
    fi
    folder=${dirs[0]}
fi

# --url was set, download the url, untar it to a temp dir, and verify it only has one
# sub dir.
if [[ -n "$url" ]]; then
    echo "Downloading plugin and extracting plugin from $url..."
    temp_work_dir=$(mktemp -d)
    curl -Ls "$url" | tar xvz -C "$temp_work_dir"

    dirs=("$temp_work_dir"/plugins/*/)
    num_dirs=${#dirs[@]}
    if [[ "$num_dirs" -ne 1 ]]; then
        echo "ERROR: The provided url does not look like a Baserow plugin. The plugin archive must contain a plugins/ sub-directory itself containing exactly one sub-directory for the plugin."
        exit 1;
    fi
    folder=${dirs[0]}
fi

# copy the plugin at the folder location into the plugin dir if it has not been already.
if [[ -n "$folder" ]]; then
  plugin_name="$(basename -- "$folder")"
  if [[ ! $folder -ef $BASEROW_PLUGIN_DIR/$plugin_name ]]; then
    echo "Copying plugin $plugin_name into plugins folder... "
    if [[ "$BASEROW_PLUGIN_DIR/$plugin_name" != "$folder" ]]; then
      mkdir -p "$BASEROW_PLUGIN_DIR"
      cp -r "$folder" "$BASEROW_PLUGIN_DIR/$plugin_name"
      folder="$BASEROW_PLUGIN_DIR/$plugin_name"
    fi
  fi
fi

# Now we've copied the plugin into the plugin dir we can delete the tmp download dir
# if we used it.
if [[ -n "${temp_work_dir:-}" ]]; then
  rm -rf "$temp_work_dir"
fi

# --hash was set, hash the plugin folder and check it matches.
if [[ -n "$hash" ]]; then
  plugin_hash=$(find "$folder" -type f -print0 | sort -z | xargs -0 sha1sum | sha1sum | cut -d " " -f 1 )
  if [[ "$plugin_hash" != "$hash" ]]; then
    echo "ERROR: The plugin does not match the provided hash. This could mean it has been maliciously modified and it is not safe to install."
    echo "The plugins hash was: $plugin_hash"
    echo "Instead we expected : $hash"
    exit 1;
  else
    echo "Plugin hash matches provided hash."
  fi
fi

check_and_run_script(){
    if [[ -f "$1/$2" ]]; then
        echo "Running plugin's custom $2 script"
        bash "$1/$2"
    fi
}

PLUGIN_BACKEND_FOLDER="$folder/backend"
plugin_name="$(basename -- "$folder")"

# Make sure we create the container markers folder which we will use to check if a
# plugin has been installed or not already inside this container.
mkdir -p /baserow/container_markers

# Install the backend plugin
if [[ -d "/baserow/backend" && -d "$PLUGIN_BACKEND_FOLDER" ]]; then
    if [[ ! -f /baserow/container_markers/$plugin_name.backend-built ]]; then
      echo "Installing backend plugin module:"

      . /baserow/venv/bin/activate
      cd /baserow/backend

      if [[ "$dev" == true ]]; then
          pip3 install -e "$PLUGIN_BACKEND_FOLDER"
      else
          pip3 install "$PLUGIN_BACKEND_FOLDER"
      fi

      check_and_run_script "$PLUGIN_BACKEND_FOLDER" build.sh
      touch /baserow/container_markers/"$plugin_name".backend-built

    else
      echo "Skipping install of $plugin_name backend plugin as it is already installed."
    fi

    if [[ ! -f /baserow/container_markers/$plugin_name.backend-runtime-setup && $runtime == "true" ]]; then
      check_and_run_script "$PLUGIN_BACKEND_FOLDER" runtime_setup.sh
      touch /baserow/container_markers/"$plugin_name".backend-runtime-setup
    fi
fi

# Install the web-frontend plugin
PLUGIN_WEBFRONTEND_FOLDER="$folder/web-frontend"
if [[ -d "/baserow/web-frontend" && -d "$PLUGIN_WEBFRONTEND_FOLDER" ]]; then
    if [[ ! -f /baserow/container_markers/$plugin_name.web-frontend-built ]]; then
      echo "Building and installing the web-frontend plugin module:"

      cd /baserow/web-frontend
      yarn add "$PLUGIN_WEBFRONTEND_FOLDER"

      if [[ "$dev" != true ]]; then
        /baserow/web-frontend/docker/docker-entrypoint.sh build-local
        chown -R "$DOCKER_USER": /baserow/web-frontend/.nuxt
      fi

      check_and_run_script "$PLUGIN_WEBFRONTEND_FOLDER" build.sh
      touch /baserow/container_markers/"$plugin_name".web-frontend-built
    else
      echo "Skipping build of $plugin_name web-frontend plugin as it has already been built."
    fi

    if [[ ! -f /baserow/container_markers/$plugin_name.web-frontend-runtime-setup && $runtime == "true" ]]; then
      check_and_run_script "$PLUGIN_WEBFRONTEND_FOLDER" runtime_setup.sh
      touch /baserow/container_markers/"$plugin_name".web-frontend-runtime-setup
    fi
fi

echo "Fixing ownership of plugins from $(id -u) to $DOCKER_USER in $BASEROW_PLUGIN_DIR"
chown -R "$DOCKER_USER": "$BASEROW_PLUGIN_DIR"

