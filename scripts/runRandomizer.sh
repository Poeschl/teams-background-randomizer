#!/usr/bin/env sh

PROJECT_FOLDER=$(cd $(dirname ${BASH_SOURCE:-$0}); cd ..; pwd)
PATH_TO_PIPENV=/opt/homebrew/bin/pipenv

cd ${PROJECT_FOLDER}
echo Runnig in $(pwd)
${PATH_TO_PIPENV} run python "teams_background_randomizer/__init__.py" "config/config.yaml"
