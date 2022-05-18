#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

show_help(){
    echo """
Usage: uninstall_plugin.sh <plugin_name>
  -h, --help                          Show this help message and exit.

Uninstalling a plugin will remove the plugin and it's dependencies from the system.
If the plugin has 'backend/uninstall.sh' or 'web-frontend/uninstall.sh' scripts, they
will also be run to do any custom per plugin uninstallation.
"""
}

name="$1"


BASEROW_PLUGIN_DIR=${BASEROW_PLUGIN_DIR:-/baserow/plugins}
folder="$BASEROW_PLUGIN_DIR/$name"

if [[ ! -d "$folder" ]]; then
    echo "Plugin '$name' not found."
    exit 1
fi


check_and_run_script(){
    if [[ -f "$1/$2" ]]; then
        echo "Running plugin's custom $2 script"
        bash "$1/$2"
    fi
}

PLUGIN_BACKEND_FOLDER="$folder/backend"
plugin_name="$(basename -- "$folder")"

if [[ -d "/baserow/backend" && -d "$PLUGIN_BACKEND_FOLDER" ]]; then
    if [[ -f /baserow/container_markers/$plugin_name.backend-installed ]]; then
      echo "Un-installing plugin $plugin_name from the backend..."
      . /baserow/venv/bin/activate
      cd /baserow/backend
      pip3 uninstall "$PLUGIN_BACKEND_FOLDER"
      check_and_run_script "$PLUGIN_BACKEND_FOLDER" uninstall.sh
      rm /baserow/container_markers/"$plugin_name".backend-installed
    else
      echo "Skipping uninstall of $plugin_name backend plugin as it is already uninstalled."
    fi
fi

PLUGIN_WEBFRONTEND_FOLDER="$folder/web-frontend"
if [[ -d "/baserow/web-frontend" && -d "$PLUGIN_WEBFRONTEND_FOLDER" ]]; then
    if [[ -f /baserow/container_markers/$plugin_name.web-frontend-installed ]]; then
      echo "Un-installing plugin $plugin_name from the web-frontend..."
      cd /baserow/web-frontend
      yarn remove "$PLUGIN_WEBFRONTEND_FOLDER"
      check_and_run_script "$PLUGIN_WEBFRONTEND_FOLDER" uninstall.sh
      rm /baserow/container_markers/"$plugin_name".web-frontend-installed
    else
      echo "Skipping uninstall of $plugin_name web-frontend plugin as it is already uninstalled."
    fi
fi

echo "Removing plugin..."
rm -rf "$folder"
