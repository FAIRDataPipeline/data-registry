#!/bin/bash
export SCRC_HOME=$HOME/.scrc
mkdir "$SCRC_HOME"
git clone https://github.com/ScottishCovidResponse/data-registry.git "$SCRC_HOME"
python3 -m venv "$SCRC_HOME"/venv
source "$SCRC_HOME"/venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install -r "$SCRC_HOME"/local-requirements.txt
export DJANGO_SETTINGS_MODULE="drams.local-settings"
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=admin
cd "$SCRC_HOME"/scripts || exit
./rebuild-local.sh